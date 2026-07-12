"""Amazon S3 storage helpers."""
import uuid
from typing import Optional

from flask import current_app
from werkzeug.datastructures import FileStorage


def upload_image(file: FileStorage, allowed_extensions: set) -> Optional[str]:
    """
    Upload a validated image file to S3.

    The file must already be validated by is_valid_image() and
    allowed_extension() before calling this function.

    Returns the S3 object key on success, None on failure.
    The key format is: uploads/<uuid>.<ext>
    """
    if not file or not file.filename:
        return None

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        return None

    key = f"uploads/{uuid.uuid4().hex}.{ext}"
    bucket = current_app.config["S3_BUCKET"]

    try:
        current_app.s3.upload_fileobj(
            file.stream,
            bucket,
            key,
            ExtraArgs={
                "ContentType": file.content_type or f"image/{ext}",
                # Server-side encryption at rest
                "ServerSideEncryption": "AES256",
                # Objects are private — accessed only via presigned URLs
                "ACL": "private",
            },
        )
        current_app.logger.info("S3 upload success: s3://%s/%s", bucket, key)
        return key
    except Exception as exc:
        current_app.logger.error("S3 upload failed [key=%s]: %s", key, exc)
        return None


def delete_image(key: str) -> bool:
    """
    Delete an object from S3.
    Silently succeeds if the object doesn't exist (idempotent).
    """
    if not key:
        return False
    bucket = current_app.config["S3_BUCKET"]
    try:
        current_app.s3.delete_object(Bucket=bucket, Key=key)
        current_app.logger.info("S3 delete success: s3://%s/%s", bucket, key)
        return True
    except Exception as exc:
        current_app.logger.error("S3 delete failed [key=%s]: %s", key, exc)
        return False


def get_presigned_url(key: str) -> Optional[str]:
    """
    Generate a time-limited presigned URL for a private S3 object.

    Presigned URLs expire after S3_PRESIGNED_EXPIRY seconds (default 1 hour).
    This means images are never directly publicly accessible — users can only
    view them via short-lived signed URLs, which is the correct security posture.
    """
    if not key:
        return None
    try:
        return current_app.s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": current_app.config["S3_BUCKET"],
                "Key": key,
            },
            ExpiresIn=current_app.config["S3_PRESIGNED_EXPIRY"],
        )
    except Exception as exc:
        current_app.logger.error("S3 presign failed [key=%s]: %s", key, exc)
        return None
