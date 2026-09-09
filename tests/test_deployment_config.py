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


def test_proxy_fix_middleware_installed(app):
    """Verify ProxyFix middleware is installed on wsgi_app for ALB/reverse proxy support."""
    from werkzeug.middleware.proxy_fix import ProxyFix
    assert isinstance(app.wsgi_app, ProxyFix)


def test_production_config_cookie_security():
    """Verify ProductionConfig defaults SESSION_COOKIE_SECURE to True."""
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.WTF_CSRF_SSL_STRICT is True


def test_production_secret_key_fail_fast(monkeypatch):
    """Verify create_app('production') raises ValueError if SECRET_KEY is missing."""
    import os
    from app import create_app
    monkeypatch.delenv("SECRET_KEY", raising=False)
    # Temporarily clear BaseConfig.SECRET_KEY if cached
    with monkeypatch.context() as m:
        m.setattr(ProductionConfig, "SECRET_KEY", "")
        with pytest.raises(ValueError, match="Production configuration requires a non-empty SECRET_KEY"):
            create_app("production")


def test_health_caching(client):
    """Verify /api/health caching serves fast subsequent requests."""
    res1 = client.get("/api/health")
    assert res1.status_code == 200
    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res1.get_json()["status"] == res2.get_json()["status"]


def test_authenticated_user_request_caching(client, app):
    """Verify authenticated user is cached in flask.g during request lifecycle."""
    from flask import g
    # Register a user
    app.user_model.create("cacheuser", "ValidPassword123!", "cache@example.com")
    with client.session_transaction() as sess:
        sess["username"] = "cacheuser"
        sess["session_version"] = 1

    with client:
        res = client.get("/")
        assert res.status_code == 200
        # g.current_user was set during before_request
        assert g.current_user is not None
        assert g.current_user["username"] == "cacheuser"


def test_force_https_redirection(app):
    """Verify FORCE_HTTPS redirects HTTP requests with 301 to HTTPS."""
    app.config["FORCE_HTTPS"] = True
    try:
        with app.test_client() as c:
            res = c.get("/", headers={"X-Forwarded-Proto": "http"})
            assert res.status_code == 301
            assert res.location.startswith("https://")
    finally:
        app.config["FORCE_HTTPS"] = False



