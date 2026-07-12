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

            current_app.logger.info(
                "Login success: '%s' from %s", username, request.remote_addr
            )
            flash(f"Welcome back, {username}! 👋", "success")

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

    POST-only + CSRF token required.
    A simple GET to /logout from a malicious link cannot log the user out.
    """
    username = session.get("username", "anonymous")
    session.clear()  # Destroy entire session, not just username key
    current_app.logger.info("Logout: '%s' from %s", username, request.remote_addr)
    flash("You've been signed out.", "info")
    return redirect(url_for("posts.index"))
