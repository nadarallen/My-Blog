"""
Authentication Blueprint — /login, /register, /logout

Security measures applied:
  - Rate limiting: 5 login attempts/min, 10 register/hour per IP
  - Username normalised to lowercase at all times
  - Username format validated (alphanumeric + underscore, 3–32 chars)
  - Password strength validated (8–72 chars, letter + digit required)
  - Argon2id password hashing via UserModel
  - Timing-safe login (no user-enumeration via response timing)
  - Logout via POST + CSRF token (prevents CSRF-triggered logout)
  - Open redirect protection on ?next= parameter
  - Session regenerated on login (session fixation prevention)
  - Permanent session with 1-hour expiry
"""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..extensions import limiter
from ..utils.security import (
    is_safe_redirect_url,
    is_valid_password,
    is_valid_username,
)

auth_bp = Blueprint("auth", __name__)


# ──────────────────────────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")  # Prevents mass account creation
def register():
    """Create a new user account."""
    # Already logged in — redirect away
    if "username" in session:
        return redirect(url_for("posts.index"))

    if request.method == "POST":
        raw_username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Normalise: lowercase + strip whitespace
        username = raw_username.strip().lower()

        # ── Validation ──────────────────────────────────────────
        error = None
        if not is_valid_username(username):
            error = "Username must be 3–32 chars, letters/numbers/underscores only."
        elif not is_valid_password(password):
            error = "Password must be 8–72 chars with at least one letter and one number."
        elif password != confirm:
            error = "Passwords do not match."

        if error:
            flash(error, "danger")
            # Re-render form — do NOT redirect (preserves form context)
            return render_template("register.html", username=raw_username), 400

        # ── Create user ─────────────────────────────────────────
        created = current_app.user_model.create(username, password)
        if not created:
            flash("Username is already taken. Please choose another.", "danger")
            return render_template("register.html", username=raw_username), 409

        current_app.logger.info(
            "New user registered: '%s' from %s", username, request.remote_addr
        )
        flash("Account created! You can now sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ──────────────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # Brute-force protection
def login():
    """Authenticate an existing user."""
    # Already logged in — redirect away
    if "username" in session:
        return redirect(url_for("posts.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        # Basic presence check (not a security measure, just UX)
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html", username=username), 400

        # Verify credentials (timing-safe inside UserModel.verify())
        if current_app.user_model.verify(username, password):
            # ── Session fixation prevention ──────────────────────
            # Clear the old session completely before setting new data
            # This prevents an attacker who obtained a pre-auth session ID
            # from reusing it post-authentication
            old_session = dict(session)
            session.clear()

            # Set session with hardened settings
            session.permanent = True  # Honour PERMANENT_SESSION_LIFETIME
            session["username"] = username

            # Store role and session version in session
            user_obj = current_app.user_model.get_by_username(username)
            if user_obj:
                admin_username = current_app.config.get("ADMIN_USERNAME", "admin")
                if username.lower() == admin_username.lower():
                    session["role"] = "admin"
                else:
                    session["role"] = user_obj.get("role", "user")
                session["session_version"] = int(user_obj.get("session_version", 1))
            else:
                session["role"] = "user"
                session["session_version"] = 1

            current_app.logger.info(
                "Login success: '%s' (role: %s, ver: %s) from %s", username, session["role"], session["session_version"], request.remote_addr
            )
            flash(f"Welcome back, {username}!", "success")

            # ── Safe redirect ─────────────────────────────────────
            # Validate ?next= to prevent open redirect attacks
            next_url = request.args.get("next") or request.form.get("next")
            if next_url and is_safe_redirect_url(next_url, request.host):
                return redirect(next_url)
            return redirect(url_for("posts.index"))

        # Generic error — never reveal whether the username exists
        current_app.logger.warning(
            "Login failure: username='%s' from %s", username, request.remote_addr
        )
        flash("Invalid username or password.", "danger")
        return render_template("login.html", username=username), 401

    return render_template("login.html")


# ──────────────────────────────────────────────────────────────────
# Logout — POST only (prevents CSRF-triggered logout)
# ──────────────────────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Sign out the current user.
    """
    username = session.get("username", "anonymous")
    session.clear()  # Destroy entire session, not just username key
    current_app.logger.info("Logout: '%s' from %s", username, request.remote_addr)
    flash("You've been signed out.", "info")
    return redirect(url_for("posts.index"))


# ──────────────────────────────────────────────────────────────────
# Author Profile Page & Settings
# ──────────────────────────────────────────────────────────────────

@auth_bp.route("/author/<username>")
def author_profile(username):
    user_obj = current_app.user_model.get_by_username(username)
    if not user_obj:
        flash("Author profile not found.", "warning")
        return redirect(url_for("posts.index"))

    posts, total = current_app.post_model.get_all_paginated(
        page=1, per_page=20, author=username, status="published"
    )
    followers = current_app.interaction_model.get_followers(username)
    following = current_app.interaction_model.get_following(username)

    is_curr_following = False
    if "username" in session:
        is_curr_following = current_app.interaction_model.is_following(session["username"], username)

    return render_template(
        "profile.html",
        profile_user=user_obj,
        posts=posts,
        total_posts=total,
        followers_count=len(followers),
        following_count=len(following),
        is_following=is_curr_following,
    )


@auth_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if "username" not in session:
        flash("Please log in to edit your profile.", "warning")
        return redirect(url_for("auth.login"))

    username = session["username"]
    user_obj = current_app.user_model.get_by_username(username)

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        website = request.form.get("website", "").strip()
        location = request.form.get("location", "").strip()
        avatar_url = request.form.get("avatar_url", "").strip()
        cover_url = request.form.get("cover_url", "").strip()

        update_data = {
            "display_name": display_name,
            "bio": bio,
            "website": website,
            "location": location,
            "avatar_url": avatar_url,
            "cover_url": cover_url,
        }
        current_app.user_model.update_profile(username, update_data)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("auth.author_profile", username=username))

    return render_template("profile_edit.html", user=user_obj)


# ──────────────────────────────────────────────────────────────────
# Password Change & Account Deletion
# ──────────────────────────────────────────────────────────────────

@auth_bp.route("/account/password", methods=["POST"])
def change_password():
    if "username" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    username = session["username"]
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")

    if not current_app.user_model.verify(username, old_password):
        flash("Current password was incorrect.", "danger")
        return redirect(url_for("auth.edit_profile"))

    if not is_valid_password(new_password):
        flash("New password must be 8–72 chars with at least one letter and one number.", "danger")
        return redirect(url_for("auth.edit_profile"))

    current_app.user_model.change_password(username, new_password)
    session.clear()
    flash("Password updated successfully. Please log in again.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/account/delete", methods=["POST"])
def delete_account():
    if "username" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    username = session["username"]
    current_app.user_model.delete_account(username)
    current_app.audit_model.log_action(
        actor=username,
        action="ACCOUNT_DELETED",
        target=username,
        ip_address=request.remote_addr or "",
    )
    session.clear()
    flash("Your account has been deleted.", "info")
    return redirect(url_for("posts.index"))


