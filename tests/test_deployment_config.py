"""
Tests for production deployment configuration, Free-Tier environment abstractions,
health endpoints, and multi-instance scheduler locking safety.
"""
import pytest
from app.config import ProductionConfig, BaseConfig
from app.services.scheduler import BackgroundScheduler


def test_production_config_hardening():
    """Verify ProductionConfig sets secure flags and disables debug mode."""
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.FLASK_ENV == "production"
    assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
    assert ProductionConfig.SESSION_COOKIE_SAMESITE == "Lax"
    assert ProductionConfig.MAX_CONTENT_LENGTH == 5 * 1024 * 1024


def test_health_endpoint(client):
    """Verify /api/health returns HTTP 200 with status and dependency info."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert data["checks"]["dynamodb"] == "ok"
    assert data["checks"]["s3"] == "ok"


def test_scheduler_lock_acquisition(app):
    """Verify BackgroundScheduler distributed lock acquisition behaves correctly."""
    scheduler = BackgroundScheduler(app)
    # Attempt acquiring lock for task
    locked = scheduler._acquire_lock("test_scheduled_task", ttl_seconds=10)
    assert locked is True
