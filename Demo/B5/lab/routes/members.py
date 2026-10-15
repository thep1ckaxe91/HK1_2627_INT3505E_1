from jsonschema import validate, ValidationError
from flask import request, jsonify, Blueprint
from models import Member, Loan, db
import json
import os

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "member.json")))

bp = Blueprint("members", __name__, url_prefix="/api/v1/members")


@bp.get("")
def list_members():
    limit = min(request.args.get("limit", 20, type=int), 100)
    rows = db.session.query(Member).order_by(Member.id).limit(limit).all()
    return jsonify([m.to_dict() for m in rows])


@bp.get("/<int:member_id>")
def get_member(member_id):
    member = db.session.get(Member, member_id)
    if not member:
        return jsonify({"error": "not_found", "message": f"Member {member_id} not found"}), 404
    return jsonify(member.to_dict())


@bp.post("")
def create_member():
    payload = request.get_json(silent=True) or {}
    try:
        validate(payload, SCHEMA)
    except ValidationError as e:
        return jsonify({
            "error": "validation_failed",
            "field": list(e.path),
            "message": e.message,
        }), 400

    if db.session.query(Member).filter_by(email=payload["email"]).first():
        return jsonify({"error": "conflict", "message": "Email already exists"}), 409

    member = Member(
        email=payload["email"],
        display_name=payload["display_name"],
        membership_type=payload.get("membership_type", "standard"),
    )
    db.session.add(member)
    db.session.commit()
    return jsonify(member.to_dict()), 201


@bp.put("/<int:member_id>")
def update_member(member_id):
    member = db.session.get(Member, member_id)
    if not member:
        return jsonify({"error": "not_found", "message": f"Member {member_id} not found"}), 404
    payload = request.get_json(silent=True) or {}
    if "email" in payload:
        existing = db.session.query(Member).filter_by(email=payload["email"]).first()
        if existing and existing.id != member_id:
            return jsonify({"error": "conflict", "message": "Email already in use"}), 409
        member.email = payload["email"]
    if "display_name" in payload:
        member.display_name = payload["display_name"]
    if "membership_type" in payload:
        if payload["membership_type"] not in ("standard", "premium", "student"):
            return jsonify({"error": "validation_failed", "message": "Invalid membership type"}), 400
        member.membership_type = payload["membership_type"]
    db.session.commit()
    return jsonify(member.to_dict())


@bp.delete("/<int:member_id>")
def delete_member(member_id):
    member = db.session.get(Member, member_id)
    if not member:
        return jsonify({"error": "not_found", "message": f"Member {member_id} not found"}), 404
    db.session.delete(member)
    db.session.commit()
    return "", 204


@bp.get("/<int:member_id>/loans")
def list_member_loans(member_id):
    member = db.session.get(Member, member_id)
    if not member:
        return jsonify({"error": "not_found", "message": f"Member {member_id} not found"}), 404
    loans = db.session.query(Loan).filter_by(member_id=member_id).all()
    return jsonify([l.to_dict() for l in loans])
