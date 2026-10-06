from flask import request, jsonify
from uuid import uuid4

ERROR_BASE = "/error"
class ApiProblem(Exception):

    def __init__(self, status, title, detail = None, type_path=None, **extra) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.type = f"{ERROR_BASE}/{type_path}" if type_path else "about:blank"
        self.extra = extra
        _problem(self.status, self.title, self.detail, type_path, **extra)

def _problem(status, title, detail=None, type_path=None, **extra):
    body = {
        "type" : f"{ERROR_BASE}/{type_path}" if type_path else "about:blank",
        "title" : title,
        "status" : status,
        "instance" : request.path,
        "trace_id" : str(uuid4())
    }
    if detail:
        body["detail"] = detail

    body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = "application/problem+json"

    return resp