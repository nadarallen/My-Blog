"""Health check and API utilities."""
import time

from flask import Blueprint, current_app, jsonify

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
