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
    app.config["START_TIME"] = _START_TIME

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

    app.post_model = PostModel(app.dynamodb, app.config["DYNAMODB_POSTS_TABLE"])
    app.user_model = UserModel(app.dynamodb, app.config["DYNAMODB_USERS_TABLE"])

    # ── Blueprints ───────────────────────────────────────────────
    from .routes.auth import auth_bp
    from .routes.posts import posts_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Context processors ───────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {"admin_username": app.config.get("ADMIN_USERNAME", "admin")}

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
