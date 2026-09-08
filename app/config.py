"""Configuration classes for different environments."""
import os
from datetime import timedelta


class BaseConfig:
    # ── Flask ──────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    MAX_CONTENT_LENGTH: int = 5 * 1024 * 1024  # 5 MB upload limit
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg", "gif", "webp"}

    # ── Session hardening ──────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = False  # Set True when HTTPS is enabled
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(hours=1)

    # ── Flask-WTF CSRF ─────────────────────────────────────────────
    WTF_CSRF_TIME_LIMIT: int = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT: bool = False

    # ── Flask-Limiter ──────────────────────────────────────────────
    RATELIMIT_STORAGE_URL: str = os.environ.get("REDIS_URL") or os.environ.get(
        "RATELIMIT_STORAGE_URL", "memory://"
    )

    # ── AWS (resolved from EC2 IAM Instance Role — no keys needed) ─
    AWS_REGION: str = os.environ.get("AWS_REGION", "ap-south-1")
    S3_BUCKET: str = os.environ.get("S3_BUCKET", "myblog-images")
    S3_PRESIGNED_EXPIRY: int = 3600  # 1 hour presigned URL lifetime
    DYNAMODB_POSTS_TABLE: str = os.environ.get("DYNAMODB_POSTS_TABLE", "myblog-posts")
    DYNAMODB_USERS_TABLE: str = os.environ.get("DYNAMODB_USERS_TABLE", "myblog-users")
    DYNAMODB_COMMENTS_TABLE: str = os.environ.get("DYNAMODB_COMMENTS_TABLE", "myblog-comments")
    DYNAMODB_INTERACTIONS_TABLE: str = os.environ.get("DYNAMODB_INTERACTIONS_TABLE", "myblog-interactions")
    DYNAMODB_NOTIFICATIONS_TABLE: str = os.environ.get("DYNAMODB_NOTIFICATIONS_TABLE", "myblog-notifications")
    DYNAMODB_AUDIT_TABLE: str = os.environ.get("DYNAMODB_AUDIT_TABLE", "myblog-audit")
    DYNAMODB_TAXONOMY_TABLE: str = os.environ.get("DYNAMODB_TAXONOMY_TABLE", "myblog-taxonomy")
    DYNAMODB_SETTINGS_TABLE: str = os.environ.get("DYNAMODB_SETTINGS_TABLE", "myblog-settings")
    DYNAMODB_REPORTS_TABLE: str = os.environ.get("DYNAMODB_REPORTS_TABLE", "myblog-reports")

    # ── App ────────────────────────────────────────────────────────
    ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "admin")
    POSTS_PER_PAGE: int = 6



class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    FLASK_ENV: str = "development"
    # In dev, boto3 reads credentials from ~/.aws/credentials or env vars
    # so the app still works locally without an EC2 instance role


class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    FLASK_ENV: str = "production"
    PROPAGATE_EXCEPTIONS: bool = False
    # In production with HTTPS, enforce secure cookie and CSRF flags
    # Can be overridden via env var for local testing without SSL
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
    WTF_CSRF_SSL_STRICT: bool = os.environ.get("WTF_CSRF_SSL_STRICT", "true").lower() == "true"
    # On EC2: IAM Instance Role provides AWS credentials automatically


config_by_name: dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
