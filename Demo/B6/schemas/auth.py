import marshmallow as ma


class LoginRequestSchema(ma.Schema):
    """Payload schema for user login authentication."""

    email = ma.fields.Email(
        required=True,
        metadata={
            "description": "User email address",
            "example": "student@vnu.edu.vn",
        },
    )
    password = ma.fields.String(
        required=True,
        load_only=True,
        metadata={
            "description": "User plain text password",
            "example": "SecretPass123!",
        },
    )


class LoginResponseSchema(ma.Schema):
    """Response schema upon successful login."""

    access_token = ma.fields.String(
        required=True,
        metadata={
            "description": "Short-lived JWT Access Token (15 mins TTL)",
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        },
    )
    refresh_token = ma.fields.String(
        required=True,
        metadata={
            "description": "Long-lived JWT Refresh Token (30 days TTL)",
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        },
    )
    token_type = ma.fields.String(
        load_default="Bearer",
        metadata={
            "description": "Token authorization type",
            "example": "Bearer",
        },
    )
    expires_in = ma.fields.Integer(
        load_default=900,
        metadata={
            "description": "Token lifetime in seconds",
            "example": 900,
        },
    )
    scopes = ma.fields.List(
        ma.fields.String(),
        required=True,
        metadata={
            "description": "Granted authorization scopes",
            "example": ["posts:read", "posts:write"],
        },
    )


class TokenRefreshResponseSchema(ma.Schema):
    """Response schema upon successful token refresh."""

    access_token = ma.fields.String(
        required=True,
        metadata={
            "description": "Newly minted JWT Access Token (15 mins TTL)",
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        },
    )
    token_type = ma.fields.String(
        load_default="Bearer",
        metadata={
            "description": "Token authorization type",
            "example": "Bearer",
        },
    )
    expires_in = ma.fields.Integer(
        load_default=900,
        metadata={
            "description": "Token lifetime in seconds",
            "example": 900,
        },
    )
