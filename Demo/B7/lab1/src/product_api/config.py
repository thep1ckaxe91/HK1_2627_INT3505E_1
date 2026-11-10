import os
from typing import Any, Dict
from sqlalchemy.pool import StaticPool


class DefaultConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-not-for-prod")
    JSON_SORT_KEYS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class TestConfig(DefaultConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    LOG_LEVEL = "WARNING"
    # StaticPool allows multiple connections in tests to share the single in-memory SQLite DB
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }


class ProductionConfig(DefaultConfig):
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }
