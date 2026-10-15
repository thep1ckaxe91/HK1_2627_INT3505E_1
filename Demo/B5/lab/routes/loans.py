from jsonschema import validate, ValidationError
from flask import request, jsonify, Blueprint
from sqlalchemy import select
from models import Loan, BookCopy, Member, db
from datetime import datetime, timezone, timedelta
import json
import os

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "loan.json")))

bp = Blueprint("loans", __name__, url_prefix="/api/v1/loans")


@bp.get("")
def list_loans():
    q = select(Loan)

    member_id = request.args.get("member_id", type=int)
    if member_id:
        q = q.filter(Loan.member_id == member_id)

    status = request.args.get("status")
    if status:
        q = q.filter(Loan.status == status)

    sort = request.args.get("sort", "-loan_date")
    if sort == "-loan_date":
        q = q.order_by(Loan.loan_date.desc(), Loan.id.desc())
    elif sort == "loan_date":
        q = q.order_by(Loan.loan_date.asc(), Loan.id.asc())
    elif sort == "-due_date":
        q = q.order_by(Loan.due_date.desc(), Loan.id.desc())
    elif sort == "due_date":
        q = q.order_by(Loan.due_date.asc(), Loan.id.asc())
    else:
        q = q.order_by(Loan.id.desc())

    limit = min(request.args.get("limit", 20, type=int), 100)
    rows = db.session.scalars(q.limit(limit)).all()
    return jsonify([l.to_dict() for l in rows])


@bp.get("/<int:loan_id>")
def get_loan(loan_id):
    loan = db.session.get(Loan, loan_id)
    if not loan:
        return jsonify({"error": "not_found", "message": f"Loan {loan_id} not found"}), 404
    return jsonify(loan.to_dict())


@bp.post("")
def create_loan():
    payload = request.get_json(silent=True) or {}
    try:
        validate(payload, SCHEMA)
    except ValidationError as e:
        return jsonify({
            "error": "validation_failed",
            "field": list(e.path),
            "message": e.message,
        }), 400

    copy = db.session.get(BookCopy, payload["copy_id"])
    if not copy:
        return jsonify({"error": "not_found", "message": f"BookCopy {payload['copy_id']} not found"}), 404

    if copy.status != "available":
        return jsonify({"error": "conflict", "message": f"Copy is not available (current status: {copy.status})"}), 409

    member = db.session.get(Member, payload["member_id"])
    if not member:
        return jsonify({"error": "not_found", "message": f"Member {payload['member_id']} not found"}), 404

    # Calculate due date: default to 14 days if not provided
    now = datetime.now(timezone.utc)
    if "due_date" in payload:
        try:
            due_date = datetime.fromisoformat(payload["due_date"]).replace(tzinfo=timezone.utc)
        except ValueError:
            return jsonify({"error": "validation_failed", "message": "Invalid date format for due_date (expected YYYY-MM-DD)"}), 400
    else:
        due_date = now + timedelta(days=14)

    loan = Loan(
        loan_date=now,
        due_date=due_date,
        status="active",
        copy_id=copy.id,
        member_id=member.id,
    )
    copy.status = "loaned"
    db.session.add(loan)
    db.session.commit()
    return jsonify(loan.to_dict()), 201


@bp.put("/<int:loan_id>/return")
def return_loan(loan_id):
    loan = db.session.get(Loan, loan_id)
    if not loan:
        return jsonify({"error": "not_found", "message": f"Loan {loan_id} not found"}), 404

    if loan.status == "returned":
        return jsonify({"error": "bad_request", "message": "Loan already returned"}), 400

    now = datetime.now(timezone.utc)
    loan.return_date = now
    loan.status = "returned"

    if loan.copy:
        loan.copy.status = "available"

    db.session.commit()
    return jsonify(loan.to_dict())
