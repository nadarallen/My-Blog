"""Health check and API utilities."""
import time

from flask import Blueprint, current_app, jsonify, render_template, request

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    """
    Liveness + readiness probe for Docker healthcheck and AWS load balancer.

    Checks:
      - DynamoDB table is reachable
      - S3 bucket is reachable

    Returns 200 if all healthy, 503 if any dependency is degraded.
    """
    result = {
        "status": "ok",
        "uptime_seconds": round(time.time() - current_app.config["START_TIME"], 1),
        "checks": {},
    }

    # ── DynamoDB check ──────────────────────────────────────────
    try:
        # table_status triggers a DescribeTable call — lightweight
        _ = current_app.post_model.table.table_status
        result["checks"]["dynamodb"] = "ok"
    except Exception as exc:
        result["checks"]["dynamodb"] = f"error: {type(exc).__name__}"
        result["status"] = "degraded"
        current_app.logger.error("Health/DynamoDB: %s", exc)

    # ── S3 check ────────────────────────────────────────────────
    try:
        current_app.s3.head_bucket(Bucket=current_app.config["S3_BUCKET"])
        result["checks"]["s3"] = "ok"
    except Exception as exc:
        result["checks"]["s3"] = f"error: {type(exc).__name__}"
        result["status"] = "degraded"
        current_app.logger.error("Health/S3: %s", exc)

    status_code = 200 if result["status"] == "ok" else 503
    return jsonify(result), status_code


# ──────────────────────────────────────────────────────────────────
# REST API v1 Endpoints & OpenAPI Documentation
# ──────────────────────────────────────────────────────────────────

@api_bp.route("/v1/posts", methods=["GET"])
def api_list_posts():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    posts, total = current_app.post_model.get_all_paginated(
        page=page, per_page=10, search=search, category=category, status="published"
    )
    for p in posts:
        p.pop("content_lower", None)
        p.pop("title_lower", None)
    return jsonify({
        "status": "success",
        "page": page,
        "total": total,
        "results": posts,
    })


@api_bp.route("/v1/posts/<post_id>", methods=["GET"])
def api_get_post(post_id):
    post = current_app.post_model.get_by_id_no_increment(post_id)
    if not post or post.get("status") != "published":
        return jsonify({"status": "error", "message": "Post not found"}), 404
    post.pop("content_lower", None)
    post.pop("title_lower", None)
    return jsonify({"status": "success", "data": post})


@api_bp.route("/v1/docs")
def api_docs():
    return render_template("api_docs.html")

