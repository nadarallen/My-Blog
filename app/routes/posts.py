"""
Posts Blueprint — /, /post/<id>, /create, /edit/<id>, /delete/<id>

Security measures applied:
  - CSRF token required on all state-changing operations (POST/delete)
  - Delete is POST-only — cannot be triggered via GET (image tag attack)
  - Edit/Delete guarded by @author_required (checks author == user OR admin)
  - File uploads validated: extension + magic bytes (content sniffing)
  - Content sanitized with bleach before storage (XSS prevention)
  - Markdown rendered server-side then sanitized before sending to client
  - S3 images served via presigned URLs (private bucket — no direct access)
  - Title length capped at 200 chars
"""
import markdown2
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..utils.decorators import author_required, login_required
from ..utils.security import (
    allowed_extension,
    is_valid_image,
    sanitize_rendered_markdown,
    sanitize_text,
)
from ..utils.storage import delete_image, get_presigned_url, upload_image

posts_bp = Blueprint("posts", __name__)


def _add_image_urls(posts: list) -> list:
    """Attach presigned S3 URLs to a list of post dicts in-place."""
    for post in posts:
        key = post.get("image_key")
        post["image_url"] = get_presigned_url(key) if key else None
    return posts


def _render_markdown(content: str) -> str:
    """Convert Markdown to sanitized HTML."""
    raw_html = markdown2.markdown(
        content,
        extras=["fenced-code-blocks", "tables", "strike", "break-on-newline", "header-ids"],
    )
    return sanitize_rendered_markdown(raw_html)


def _handle_image_upload():
    """
    Validate and upload an image from the current request.
    Returns (image_key, error_message). One of them will be None.
    """
    file = request.files.get("image")
    if not file or not file.filename:
        return None, None  # No file provided — acceptable

    allowed = current_app.config["ALLOWED_EXTENSIONS"]

    if not allowed_extension(file.filename, allowed):
        return None, "Invalid file type. Allowed: PNG, JPG, GIF, WebP."

    if not is_valid_image(file.stream):
        return None, "File content is not a valid image (magic byte check failed)."

    key = upload_image(file, allowed)
    if not key:
        return None, "Image upload failed. Please try again."

    return key, None


# ──────────────────────────────────────────────────────────────────
# Index — post grid with pagination and search
# ──────────────────────────────────────────────────────────────────

@posts_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    # Clamp page to reasonable bounds
    page = max(1, min(page, 9999))
    search = request.args.get("q", "").strip()

    per_page = current_app.config["POSTS_PER_PAGE"]
    posts, total = current_app.post_model.get_all_paginated(page, per_page, search)
    _add_image_urls(posts)

    total_pages = max(1, -(-total // per_page))  # Ceiling division

    return render_template(
        "index.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        search=search,
        total=total,
    )


# ──────────────────────────────────────────────────────────────────
# View post
# ──────────────────────────────────────────────────────────────────

@posts_bp.route("/post/<post_id>")
def view_post(post_id: str):
    post = current_app.post_model.get_by_id(post_id)
    if not post:
        abort(404)

    post["image_url"] = get_presigned_url(post.get("image_key")) if post.get("image_key") else None
    post["content_html"] = _render_markdown(post.get("content", ""))

    return render_template("view.html", post=post)


# ──────────────────────────────────────────────────────────────────
# Create post
# ──────────────────────────────────────────────────────────────────

@posts_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        # Sanitize title (strip all HTML tags)
        title = sanitize_text(request.form.get("title", ""))
        # Keep content as Markdown — sanitization happens at render time
        content = request.form.get("content", "").strip()

        # ── Field validation ─────────────────────────────────────
        if not title:
            flash("Title is required.", "danger")
            return render_template("create.html", title=title, content=content), 400
        if len(title) > 200:
            flash("Title must be 200 characters or less.", "danger")
            return render_template("create.html", title=title, content=content), 400
        if not content:
            flash("Content is required.", "danger")
            return render_template("create.html", title=title, content=content), 400
        if len(content) > 50_000:
            flash("Content is too long (max 50,000 characters).", "danger")
            return render_template("create.html", title=title, content=content), 400

        # ── Image upload ─────────────────────────────────────────
        image_key, upload_error = _handle_image_upload()
        if upload_error:
            flash(upload_error, "danger")
            return render_template("create.html", title=title, content=content), 400

        # ── Persist ──────────────────────────────────────────────
        post_id = current_app.post_model.create(
            title=title,
            content=content,
            author=session["username"],
            image_key=image_key,
        )
        current_app.logger.info(
            "Post created [id=%s] by '%s'", post_id, session["username"]
        )
        flash("Post published! ✨", "success")
        return redirect(url_for("posts.view_post", post_id=post_id))

    return render_template("create.html")


# ──────────────────────────────────────────────────────────────────
# Edit post — author or admin only
# ──────────────────────────────────────────────────────────────────

@posts_bp.route("/edit/<post_id>", methods=["GET", "POST"])
@author_required  # Checks login + ownership; injects `post` kwarg
def edit_post(post_id: str, post: dict):
    if request.method == "POST":
        title = sanitize_text(request.form.get("title", ""))
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("Title and content are required.", "danger")
            return render_template("edit.html", post=post), 400
        if len(title) > 200:
            flash("Title must be 200 characters or less.", "danger")
            return render_template("edit.html", post=post), 400

        # ── Optional image replacement ────────────────────────────
        image_key = post.get("image_key")  # Keep existing by default
        new_key, upload_error = _handle_image_upload()
        if upload_error:
            flash(upload_error, "danger")
            return render_template("edit.html", post=post), 400
        if new_key:
            # Delete old image from S3 before replacing
            if image_key:
                delete_image(image_key)
            image_key = new_key

        current_app.post_model.update(post_id, title, content, image_key)
        current_app.logger.info(
            "Post updated [id=%s] by '%s'", post_id, session["username"]
        )
        flash("Post updated successfully.", "success")
        return redirect(url_for("posts.view_post", post_id=post_id))

    # GET — render edit form with current post data
    post["image_url"] = get_presigned_url(post.get("image_key")) if post.get("image_key") else None
    return render_template("edit.html", post=post)


# ──────────────────────────────────────────────────────────────────
# Delete post — POST only + CSRF token + author/admin check
# ──────────────────────────────────────────────────────────────────

@posts_bp.route("/delete/<post_id>", methods=["POST"])
@author_required  # Checks login + ownership
def delete_post(post_id: str, post: dict):
    """
    Delete a post. POST-only to prevent CSRF via image-tag GET requests.
    The CSRF token in the form is validated by Flask-WTF automatically.
    """
    # Delete associated S3 image first (if any)
    image_key = post.get("image_key")
    if image_key:
        delete_image(image_key)

    current_app.post_model.delete(post_id)
    current_app.logger.info(
        "Post deleted [id=%s] by '%s'", post_id, session["username"]
    )
    flash("Post deleted.", "info")
    return redirect(url_for("posts.index"))
