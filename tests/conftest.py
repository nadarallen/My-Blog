"""
pytest fixtures for OWASP security test suite.

All AWS services (DynamoDB + S3) are mocked using moto — no real
AWS credentials or internet connection required to run these tests.
"""
import io
import os
import struct

import boto3
import pytest
from moto import mock_aws

# ── Set environment BEFORE importing the app ──────────────────────
# This prevents startup errors from missing env vars
os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-long!!"
os.environ["AWS_REGION"] = "ap-south-1"
os.environ["S3_BUCKET"] = "test-myblog-images"
os.environ["DYNAMODB_POSTS_TABLE"] = "myblog-posts-test"
os.environ["DYNAMODB_USERS_TABLE"] = "myblog-users-test"
os.environ["DYNAMODB_COMMENTS_TABLE"] = "myblog-comments-test"
os.environ["DYNAMODB_INTERACTIONS_TABLE"] = "myblog-interactions-test"
os.environ["DYNAMODB_NOTIFICATIONS_TABLE"] = "myblog-notifications-test"
os.environ["DYNAMODB_AUDIT_TABLE"] = "myblog-audit-test"
os.environ["DYNAMODB_TAXONOMY_TABLE"] = "myblog-taxonomy-test"
os.environ["DYNAMODB_SETTINGS_TABLE"] = "myblog-settings-test"
os.environ["DYNAMODB_REPORTS_TABLE"] = "myblog-reports-test"
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["FLASK_ENV"] = "development"
# Fake credentials so boto3 doesn't try real AWS
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"


def _create_aws_resources():
    """Create DynamoDB tables and S3 bucket inside moto mock."""
    ddb = boto3.resource("dynamodb", region_name="ap-south-1")

    tables = [
        ("myblog-posts-test", "post_id"),
        ("myblog-users-test", "username"),
        ("myblog-comments-test", "comment_id"),
        ("myblog-interactions-test", "interaction_id"),
        ("myblog-notifications-test", "notification_id"),
        ("myblog-audit-test", "log_id"),
        ("myblog-taxonomy-test", "item_id"),
        ("myblog-settings-test", "key"),
        ("myblog-reports-test", "report_id"),
    ]

    for table_name, pk in tables:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": pk, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": pk, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    s3 = boto3.client("s3", region_name="ap-south-1")
    s3.create_bucket(
        Bucket="test-myblog-images",
        CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
    )



# ─────────────────────────────────────────────────────────────────
# Core app fixture — CSRF disabled, rate limits disabled
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def app():
    """
    Flask app with mocked AWS, CSRF disabled, rate limits disabled.
    Used for the majority of functional tests.
    """
    with mock_aws():
        _create_aws_resources()

        from app import create_app

        flask_app = create_app("development")
        flask_app.config.update(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,   # Disable CSRF for most tests
                "RATELIMIT_ENABLED": False,  # Disable rate limits for most tests
            }
        )
        yield flask_app


@pytest.fixture(scope="function")
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


# ─────────────────────────────────────────────────────────────────
# CSRF-enabled app fixture — specifically for CSRF tests
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def csrf_app():
    """
    Flask app with CSRF ENABLED.
    Used specifically to verify CSRF protection works.
    """
    with mock_aws():
        _create_aws_resources()

        from app import create_app

        flask_app = create_app("development")
        flask_app.config.update(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": True,    # ← CSRF ON
                "WTF_CSRF_CHECK_DEFAULT": True,
                "RATELIMIT_ENABLED": False,
            }
        )
        yield flask_app


@pytest.fixture(scope="function")
def csrf_client(csrf_app):
    return csrf_app.test_client()


# ─────────────────────────────────────────────────────────────────
# Rate-limit-enabled app fixture — specifically for rate limit tests
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def rate_app():
    """
    Fresh Flask app with rate limiting ENABLED.
    scope=function so each test gets a clean rate-limit counter.
    """
    with mock_aws():
        _create_aws_resources()

        from app import create_app

        flask_app = create_app("development")
        flask_app.config.update(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "RATELIMIT_ENABLED": True,   # ← RATE LIMITS ON
                "RATELIMIT_STORAGE_URL": "memory://",
            }
        )
        yield flask_app


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def register_user(client, username="testuser", password="Pass1234"):
    """Register a test user and return the response."""
    return client.post(
        "/register",
        data={"username": username, "password": password, "confirm_password": password},
        follow_redirects=False,
    )


def login_user(client, username="testuser", password="Pass1234"):
    """Log in a test user and return the response."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def create_post(client, title="Test Post", content="Hello World content here."):
    """Create a post and return the response."""
    return client.post(
        "/create",
        data={"title": title, "content": content},
        follow_redirects=False,
    )


def get_post_id_from_redirect(response) -> str:
    """Extract post_id from a redirect Location header like /post/<id>."""
    location = response.headers.get("Location", "")
    return location.rstrip("/").split("/")[-1]


# ── Image byte helpers ─────────────────────────────────────────────

def make_jpeg_bytes() -> bytes:
    """Return minimal valid JPEG file bytes (magic bytes + EOF marker)."""
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"


def make_png_bytes() -> bytes:
    """Return minimal valid PNG file bytes."""
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def make_fake_jpeg_bytes() -> bytes:
    """Return a text file disguised as a JPEG (should be rejected)."""
    return b"This is definitely not an image file, just text content."
