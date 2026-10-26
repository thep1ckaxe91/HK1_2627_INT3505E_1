import marshmallow as ma


class PostPathSchema(ma.Schema):
    """Path parameter schema for post operations."""

    id = ma.fields.Integer(
        required=True,
        metadata={
            "description": "Unique numeric identifier of the post",
            "example": 1,
        },
    )


class PostResponseSchema(ma.Schema):
    """Schema for returning post data."""

    id = ma.fields.Integer(
        required=True,
        metadata={"description": "Unique post ID", "example": 1},
    )
    author_id = ma.fields.String(
        required=True,
        metadata={"description": "User ID of the post author", "example": "1"},
    )
    title = ma.fields.String(
        required=True,
        metadata={
            "description": "Post title",
            "example": "High Performance Low-Latency Networking in C++",
        },
    )
    content = ma.fields.String(
        required=True,
        metadata={
            "description": "Post text body",
            "example": "Exploring epoll, io_uring, and lock-free ring buffers.",
        },
    )
    is_private = ma.fields.Boolean(
        required=True,
        metadata={
            "description": "Whether the post is private to the author",
            "example": False,
        },
    )
    created_at = ma.fields.String(
        required=True,
        metadata={
            "description": "Creation timestamp in ISO-8601 format",
            "example": "2026-10-27T00:00:00Z",
        },
    )
