"""Amazon S3 storage helpers."""
import io
import uuid
from typing import Optional, Tuple

from flask import current_app
from PIL import Image, ImageOps
from werkzeug.datastructures import FileStorage


def compress_and_optimize_image(
    file_stream,
    ext: str,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 82,
) -> Tuple[io.BytesIO, str]:
    """
    Compress and optimize an image stream using Pillow.
    - Resizes images exceeding max dimensions while preserving aspect ratio.
    - Compresses JPEG/WebP/PNG to reduce byte size and improve page load performance.
    - Preserves animated GIFs.
    Returns (BytesIO_stream, content_type).
    """
    ext = ext.lower()
    if ext == "jpg":
        ext = "jpeg"

    # Preserved animated GIFs without breaking frames
    if ext == "gif":
        file_stream.seek(0)
        buf = io.BytesIO(file_stream.read())
        buf.seek(0)
        return buf, "image/gif"

    try:
        file_stream.seek(0)
        img = Image.open(file_stream)

        # Transpose image based on EXIF orientation metadata
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Resize large images
        orig_w, orig_h = img.size
        if orig_w > max_width or orig_h > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        output_stream = io.BytesIO()

        if ext in ("jpeg", "jpg"):
            if img.mode in ("RGBA", "P", "LA"):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img.convert("RGBA"))
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")
            img.save(output_stream, format="JPEG", quality=quality, optimize=True)
            content_type = "image/jpeg"
        elif ext == "webp":
            img.save(output_stream, format="WEBP", quality=quality, method=4)
            content_type = "image/webp"
        elif ext == "png":
            img.save(output_stream, format="PNG", optimize=True)
            content_type = "image/png"
        else:
            file_stream.seek(0)
            output_stream = io.BytesIO(file_stream.read())
            content_type = f"image/{ext}"

        output_stream.seek(0)
        return output_stream, content_type
    except Exception as err:
        current_app.logger.warning("Image compression fallback to raw stream: %s", err)
        file_stream.seek(0)
        fallback = io.BytesIO(file_stream.read())
        fallback.seek(0)
        return fallback, f"image/{ext}"


def upload_image(file: FileStorage, allowed_extensions: set) -> Optional[str]:
    """
    Upload a validated and compressed image file to S3.

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
        compressed_stream, content_type = compress_and_optimize_image(file.stream, ext)

        current_app.s3.upload_fileobj(
            compressed_stream,
            bucket,
            key,
            ExtraArgs={
                "ContentType": content_type,
                # Server-side encryption at rest
                "ServerSideEncryption": "AES256",
                # Objects are private — accessed only via presigned URLs
                "ACL": "private",
            },
        )
        current_app.logger.info("S3 upload success (optimized): s3://%s/%s", bucket, key)
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
