"""
Application factory — My Blog.

Usage:
    from app import create_app
    app = create_app("production")
"""
import logging
import os
import time
from logging.handlers import RotatingFileHandler

import boto3
from flask import Flask, render_template

from .config import config_by_name
from .extensions import csrf, limiter

_START_TIME = time.time()


def create_app(config_name: str = "production") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )

    # ── Config ──────────────────────────────────────────────────
    app.config.from_object(config_by_name.get(config_name, config_by_name["production"]))
    if config_name == "production" and not app.config.get("SECRET_KEY"):
        raise ValueError("Production configuration requires a non-empty SECRET_KEY environment variable.")
    app.config["START_TIME"] = _START_TIME

    # ── Reverse proxy support (ALB / CloudFront / Nginx) ────────
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1,
    )

    # ── Flask extensions ─────────────────────────────────────────
    csrf.init_app(app)
    limiter.init_app(app)

    # ── AWS clients (use IAM role on EC2 — no keys needed) ───────
    region = app.config["AWS_REGION"]
    app.dynamodb = boto3.resource("dynamodb", region_name=region)
    app.s3 = boto3.client("s3", region_name=region)

    # ── Models ───────────────────────────────────────────────────
    from .models.post import PostModel
    from .models.user import UserModel
    from .models.comment import CommentModel
    from .models.interaction import InteractionModel
    from .models.notification import NotificationModel
    from .models.audit import AuditModel
    from .models.category_tag import CategoryTagModel
    from .models.settings import SettingsModel
    from .models.report import ReportModel

    app.post_model = PostModel(app.dynamodb, app.config["DYNAMODB_POSTS_TABLE"])
    app.user_model = UserModel(app.dynamodb, app.config["DYNAMODB_USERS_TABLE"])
    app.comment_model = CommentModel(app.dynamodb, app.config.get("DYNAMODB_COMMENTS_TABLE", "myblog-comments"))
    app.interaction_model = InteractionModel(app.dynamodb, app.config.get("DYNAMODB_INTERACTIONS_TABLE", "myblog-interactions"))
    app.notification_model = NotificationModel(app.dynamodb, app.config.get("DYNAMODB_NOTIFICATIONS_TABLE", "myblog-notifications"))
    app.audit_model = AuditModel(app.dynamodb, app.config.get("DYNAMODB_AUDIT_TABLE", "myblog-audit"))
    app.taxonomy_model = CategoryTagModel(app.dynamodb, app.config.get("DYNAMODB_TAXONOMY_TABLE", "myblog-taxonomy"))
    app.settings_model = SettingsModel(app.dynamodb, app.config.get("DYNAMODB_SETTINGS_TABLE", "myblog-settings"))
    app.report_model = ReportModel(app.dynamodb, app.config.get("DYNAMODB_REPORTS_TABLE", "myblog-reports"))

    # Ensure admin user has admin role
    admin_user = app.config.get("ADMIN_USERNAME", "admin")
    if app.user_model.exists(admin_user):
        app.user_model.update_role(admin_user, "admin")

    # ── Services ─────────────────────────────────────────────────
    from .services.scheduler import scheduler
    scheduler.init_app(app)

    # ── Blueprints ───────────────────────────────────────────────
    from .routes.auth import auth_bp
    from .routes.posts import posts_bp
    from .routes.social import social_bp
    from .routes.comments import comments_bp
    from .routes.taxonomy import taxonomy_bp
    from .routes.search import search_bp
    from .routes.analytics import analytics_bp
    from .routes.admin import admin_bp
    from .routes.seo_rss import seo_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(taxonomy_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(seo_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── In-Memory Read Caches (TTL: 60s) to minimize DynamoDB RCUs ───
    _cache = {
        "categories": {"data": None, "expires": 0},
        "settings": {"data": None, "expires": 0},
    }

    def _get_cached_categories():
        now = time.time()
        cached = _cache["categories"]
        if cached["data"] is not None and now < cached["expires"]:
            return cached["data"]
        try:
            data = app.taxonomy_model.list_categories()
            _cache["categories"] = {"data": data, "expires": now + 60}
            return data
        except Exception:
            return cached["data"] or []

    def _get_cached_settings():
        now = time.time()
        cached = _cache["settings"]
        if cached["data"] is not None and now < cached["expires"]:
            return cached["data"]
        try:
            data = app.settings_model.get_settings()
            _cache["settings"] = {"data": data, "expires": now + 60}
            return data
        except Exception:
            return cached["data"] or {}

    # ── Context processors ───────────────────────────────────────
    @app.context_processor
    def inject_globals():
        unread_count = 0
        from flask import session, g
        # Re-use user object resolved during validate_user_session (zero duplicate DB calls)
        current_user = getattr(g, "current_user", None)
        if current_user is None and "username" in session:
            current_user = app.user_model.get_by_username(session["username"])
            g.current_user = current_user

        if current_user:
            notifs = app.notification_model.get_user_notifications(session["username"])
            unread_count = sum(1 for n in notifs if not n.get("read"))

        categories = _get_cached_categories()
        settings = _get_cached_settings()
        return {
            "admin_username": app.config.get("ADMIN_USERNAME", "admin"),
            "current_user_obj": current_user,
            "unread_count": unread_count,
            "global_categories": categories,
            "site_settings": settings,
        }

    # ── Session Validation Middleware ────────────────────────────
    @app.before_request
    def validate_user_session():
        from flask import session, redirect, url_for, flash, request, g
        g.current_user = None
        # Skip static assets and public health check
        if request.endpoint in ("static", "api.health"):
            return None

        if "username" in session:
            user = app.user_model.get_by_username(session["username"])
            if not user or user.get("status") in ("suspended", "banned"):
                session.clear()
                if request.endpoint not in ("auth.login", "auth.register", "posts.index"):
                    flash("Your account has been deactivated or suspended.", "danger")
                    return redirect(url_for("auth.login"))
            elif user:
                expected_ver = int(user.get("session_version", 1))
                actual_ver = int(session.get("session_version", 1))
                if actual_ver < expected_ver:
                    session.clear()
                    if request.endpoint not in ("auth.login", "auth.register", "posts.index"):
                        flash("Your session has expired. Please sign in again.", "warning")
                        return redirect(url_for("auth.login"))
                g.current_user = user

    # ── Production Security Headers Middleware ───────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        return response

    # ── Error handlers ───────────────────────────────────────────
    _register_error_handlers(app)

    # ── Logging ──────────────────────────────────────────────────
    _setup_logging(app)

    return app



def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("500 Internal Error: %s", str(e))
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def too_many_requests(_e):
        from flask import flash, redirect, url_for, request
        flash("Too many attempts. Please wait a moment and try again.", "danger")
        return redirect(request.referrer or url_for("posts.index"))

    @app.errorhandler(400)
    def bad_request(_e):
        from flask import flash, redirect, url_for
        flash("Invalid request. Please try again.", "danger")
        return redirect(url_for("posts.index"))


def _setup_logging(app: Flask) -> None:
    os.makedirs("logs", exist_ok=True)
    if not app.debug:
        handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
