import marshmallow as ma


class ErrorResponseSchema(ma.Schema):
    """Standard error response schema."""

    code = ma.fields.Integer(
        required=True,
        metadata={"description": "HTTP status code", "example": 401},
    )
    status = ma.fields.String(
        required=True,
        metadata={"description": "HTTP status text", "example": "Unauthorized"},
    )
    message = ma.fields.String(
        required=True,
        metadata={
            "description": "Descriptive human-readable error message",
            "example": "Invalid credentials provided.",
        },
    )
    error_type = ma.fields.String(
        load_default="AUTHENTICATION_ERROR",
        metadata={
            "description": "Domain-specific error code",
            "example": "INVALID_CREDENTIALS",
        },
    )


class ValidationErrorSchema(ma.Schema):
    """Schema for input validation and schema mismatch errors (422/400)."""

    code = ma.fields.Integer(
        required=True,
        metadata={"description": "HTTP status code", "example": 422},
    )
    status = ma.fields.String(
        required=True,
        metadata={"description": "HTTP status text", "example": "Unprocessable Entity"},
    )
    errors = ma.fields.Dict(
        keys=ma.fields.String(),
        values=ma.fields.List(ma.fields.String()),
        metadata={
            "description": "Mapping of field names to validation failure reasons",
            "example": {"email": ["Not a valid email address."]},
        },
    )
