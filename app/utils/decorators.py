"""Route decorators for authentication and authorization."""
from functools import wraps

from flask import abort, current_app, flash, redirect, session, url_for


def login_required(f):
    """
    Redirect unauthenticated users to the login page.
    Preserves the original URL in the `next` query param.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to continue.", "warning")
            from flask import request
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def author_required(f):
    """
    Ensures the logged-in user is the post author OR the admin.

    - Reads `post_id` from URL kwargs
    - Fetches the post from DynamoDB (WITHOUT view increment)
    - Returns 404 if post doesn't exist
    - Returns 403-redirect if user is not author/admin
    - Injects `post` into the view kwargs on success

    Usage:
        @posts_bp.route("/edit/<post_id>", methods=["GET", "POST"])
        @author_required
        def edit_post(post_id, post):
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Auth check first
        if "username" not in session:
            flash("Please log in to continue.", "warning")
            from flask import request
            return redirect(url_for("auth.login", next=request.path))

        post_id = kwargs.get("post_id")
        if not post_id:
            abort(400)

        # Fetch post WITHOUT incrementing view counter
        post = current_app.post_model.get_by_id_no_increment(post_id)

        if post is None:
            abort(404)

        current_user = session["username"]
        admin = current_app.config.get("ADMIN_USERNAME", "")

        # Authorization check — must be author OR admin
        if post.get("author") != current_user and current_user != admin:
            flash("You are not authorized to perform this action.", "danger")
            return redirect(url_for("posts.index"))

        # Inject the fetched post into the view's kwargs
        kwargs["post"] = post
        return f(*args, **kwargs)

    return decorated


def role_required(*allowed_roles):
    """
    Restrict route access to specified RBAC roles.
    Checks session['role'] and verifies user status.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "username" not in session:
                flash("Please log in to continue.", "warning")
                from flask import request
                return redirect(url_for("auth.login", next=request.path))

            user_role = session.get("role", "user")
            current_user = session.get("username", "")
            admin = current_app.config.get("ADMIN_USERNAME", "admin")

            # Admin bypass
            if current_user.lower() == admin.lower():
                return f(*args, **kwargs)

            if user_role not in allowed_roles:
                flash("Access denied. Insufficient permissions.", "danger")
                return redirect(url_for("posts.index"))

            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    """Shortcut decorator for admin-only routes."""
    return role_required("admin")(f)


def moderator_required(f):
    """Shortcut decorator for moderator & admin routes."""
    return role_required("moderator", "admin")(f)

