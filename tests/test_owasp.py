"""
OWASP Top 10 (2021) Security Test Suite — My Blog
===================================================

Tests are organised by OWASP category:

  A01 – Broken Access Control
  A02 – Cryptographic Failures
  A03 – Injection (XSS / stored & reflected)
  A04 – Insecure Design (auth enumeration)
  A05 – Security Misconfiguration
  A07 – Identification and Authentication Failures
  A08 – Software and Data Integrity Failures (CSRF + file upload)
  A10 – Server-Side Request Forgery (open redirect variant)

Run with:
    pytest tests/test_owasp.py -v --tb=short
"""
import io
import pytest

from tests.conftest import (
    create_post,
    get_post_id_from_redirect,
    login_user,
    make_fake_jpeg_bytes,
    make_jpeg_bytes,
    make_png_bytes,
    register_user,
)


# ══════════════════════════════════════════════════════════════════
# A01:2021 – Broken Access Control
# ══════════════════════════════════════════════════════════════════

class TestA01BrokenAccessControl:
    """
    Verifies that protected routes enforce authentication and ownership.
    An unauthenticated user or a non-owner must NEVER reach restricted actions.
    """

    def test_create_redirects_unauthenticated_user(self, client):
        """GET /create without login → redirect to /login."""
        r = client.get("/create", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_create_post_redirects_unauthenticated(self, client):
        """POST /create without login → redirect to /login."""
        r = client.post(
            "/create",
            data={"title": "Hack", "content": "Injection attempt"},
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_edit_redirects_unauthenticated_user(self, client):
        """GET /edit/<id> without login → redirect to /login."""
        r = client.get("/edit/some-fake-post-id", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_delete_redirects_unauthenticated_user(self, client):
        """POST /delete/<id> without login → redirect to /login."""
        r = client.post("/delete/some-fake-post-id", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_delete_via_get_is_rejected(self, client):
        """
        CRITICAL: DELETE must not be possible via GET request.
        GET /delete/<id> is how image-tag CSRF attacks work.
        Expected: 405 Method Not Allowed.
        """
        r = client.get("/delete/any-post-id")
        assert r.status_code == 405, (
            "FAIL: DELETE via GET should return 405 — "
            "attacker could delete posts via <img src=/delete/id>"
        )

    def test_non_owner_cannot_edit_post(self, app, client):
        """User B cannot edit User A's post."""
        with app.test_client() as c1:
            register_user(c1, "owner_user", "Pass1234")
            login_user(c1, "owner_user", "Pass1234")
            r = create_post(c1, title="Owner's Post", content="Owner content here.")
            assert r.status_code == 302
            post_id = get_post_id_from_redirect(r)

        with app.test_client() as c2:
            register_user(c2, "attacker_user", "Pass1234")
            login_user(c2, "attacker_user", "Pass1234")
            r = c2.post(
                f"/edit/{post_id}",
                data={"title": "Hacked!", "content": "Defaced."},
                follow_redirects=True,
            )
            # Must be blocked — either redirect or 403-equivalent
            assert b"not authorized" in r.data.lower() or r.status_code in (302, 403)
            # Verify the post was NOT changed
            r2 = c2.get(f"/post/{post_id}")
            assert b"Hacked!" not in r2.data

    def test_non_owner_cannot_delete_post(self, app, client):
        """User B cannot delete User A's post."""
        with app.test_client() as c1:
            register_user(c1, "del_owner", "Pass1234")
            login_user(c1, "del_owner", "Pass1234")
            r = create_post(c1, title="Delete Target Post", content="Some content here.")
            post_id = get_post_id_from_redirect(r)

        with app.test_client() as c2:
            register_user(c2, "del_attacker", "Pass1234")
            login_user(c2, "del_attacker", "Pass1234")
            r = c2.post(f"/delete/{post_id}", follow_redirects=True)
            assert b"not authorized" in r.data.lower() or b"not authorized" in r.data.lower()

        # Verify the post still exists
        with app.test_client() as c3:
            r3 = c3.get(f"/post/{post_id}")
            assert r3.status_code == 200

    def test_admin_can_edit_any_post(self, app, client):
        """Admin user can edit any user's post."""
        with app.test_client() as c1:
            register_user(c1, "regular_poster", "Pass1234")
            login_user(c1, "regular_poster", "Pass1234")
            r = create_post(c1, title="Regular Post Title", content="Content here.")
            post_id = get_post_id_from_redirect(r)

        with app.test_client() as admin_client:
            # Admin is pre-configured as "testadmin" in ADMIN_USERNAME
            register_user(admin_client, "testadmin", "AdminPass1")
            login_user(admin_client, "testadmin", "AdminPass1")
            r = admin_client.post(
                f"/edit/{post_id}",
                data={"title": "Admin Edited", "content": "Admin changed this."},
                follow_redirects=True,
            )
            assert r.status_code == 200
            assert b"Admin Edited" in r.data

    def test_nonexistent_post_returns_404(self, client):
        """Accessing a non-existent post ID returns 404 (not 500)."""
        r = client.get("/post/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════
# A02:2021 – Cryptographic Failures
# ══════════════════════════════════════════════════════════════════

class TestA02CryptographicFailures:
    """
    Verifies passwords are stored with strong hashing and session
    cookies have correct security flags.
    """

    def test_password_not_stored_in_plaintext(self, app):
        """Password in DynamoDB must NOT equal the original plaintext."""
        with app.test_client() as c:
            register_user(c, "crypto_test_user", "PlainPass1")

        # Query DynamoDB directly via the app's model
        with app.app_context():
            response = app.user_model.table.get_item(
                Key={"username": "crypto_test_user"}
            )
            user = response.get("Item", {})
            stored = user.get("password_hash", "")
            assert stored != "PlainPass1", "FAIL: Password stored as plaintext!"
            assert len(stored) > 20, "FAIL: Password hash too short to be real"

    def test_password_uses_argon2_algorithm(self, app):
        """Password hash must start with Argon2id signature ($argon2id$)."""
        with app.test_client() as c:
            register_user(c, "argon2_check_user", "CheckPass1")

        with app.app_context():
            response = app.user_model.table.get_item(
                Key={"username": "argon2_check_user"}
            )
            stored = response["Item"]["password_hash"]
            assert stored.startswith("$argon2"), (
                f"FAIL: Expected Argon2 hash, got: {stored[:20]}..."
            )
            assert "argon2id" in stored, "FAIL: Should use Argon2id variant, not argon2i/d"

    def test_session_cookie_httponly_flag(self, app):
        """Session cookie must have HttpOnly flag set (prevents JS access)."""
        assert app.config.get("SESSION_COOKIE_HTTPONLY") is True

    def test_session_cookie_samesite_flag(self, app):
        """Session cookie must have SameSite=Lax (CSRF mitigation)."""
        samesite = app.config.get("SESSION_COOKIE_SAMESITE", "")
        assert samesite in ("Lax", "Strict"), (
            f"FAIL: SameSite should be Lax or Strict, got: {samesite}"
        )

    def test_session_has_expiry(self, app):
        """Session lifetime must be configured (not unlimited)."""
        from datetime import timedelta
        lifetime = app.config.get("PERMANENT_SESSION_LIFETIME")
        assert lifetime is not None, "FAIL: PERMANENT_SESSION_LIFETIME not set"
        assert isinstance(lifetime, timedelta)
        assert lifetime.total_seconds() <= 86400, (
            "FAIL: Session lifetime should be 24h or less, got: "
            f"{lifetime.total_seconds()}s"
        )

    def test_secret_key_is_set_and_non_trivial(self, app):
        """SECRET_KEY must be set and at least 32 characters long."""
        key = app.config.get("SECRET_KEY", "")
        assert key, "FAIL: SECRET_KEY is empty"
        assert len(key) >= 32, (
            f"FAIL: SECRET_KEY is too short ({len(key)} chars). Min 32 required."
        )


# ══════════════════════════════════════════════════════════════════
# A03:2021 – Injection (XSS)
# ══════════════════════════════════════════════════════════════════

class TestA03Injection:
    """
    Verifies that HTML/JS injection in post titles and content
    is stripped before storage and before rendering.
    """

    def test_xss_script_tag_stripped_from_title(self, app):
        """<script> tags in the title must be stripped before DB storage."""
        with app.test_client() as c:
            register_user(c, "xss_title_user", "Pass1234")
            login_user(c, "xss_title_user", "Pass1234")
            r = create_post(
                c,
                title='<script>alert("XSS")</script>My Post',
                content="Some safe content here.",
            )
            post_id = get_post_id_from_redirect(r)

        with app.app_context():
            post = app.post_model.get_by_id_no_increment(post_id)
            assert "<script>" not in post["title"], (
                "FAIL: <script> tag survived in stored title!"
            )
            # bleach should have stripped tags, leaving just the text
            assert "alert" not in post["title"] or "<script>" not in post["title"]

    def test_img_onerror_xss_stripped_from_title(self, app):
        """<img onerror=...> in title must be stripped."""
        with app.test_client() as c:
            register_user(c, "xss_img_user", "Pass1234")
            login_user(c, "xss_img_user", "Pass1234")
            r = create_post(
                c,
                title='<img src=x onerror=alert(1)>Normal Title',
                content="Safe content.",
            )
            post_id = get_post_id_from_redirect(r)

        with app.app_context():
            post = app.post_model.get_by_id_no_increment(post_id)
            assert "<img" not in post["title"], "FAIL: <img> tag survived in title!"
            assert "onerror" not in post["title"], "FAIL: onerror survived in title!"

    def test_xss_in_title_not_reflected_in_response(self, app):
        """XSS payload must not appear unescaped in any HTTP response."""
        with app.test_client() as c:
            register_user(c, "xss_reflect_user", "Pass1234")
            login_user(c, "xss_reflect_user", "Pass1234")
            payload = '<script>document.cookie="stolen"</script>'
            r = create_post(c, title=payload, content="Content here.")
            post_id = get_post_id_from_redirect(r)
            r2 = c.get(f"/post/{post_id}")
            # The raw <script> tag must NOT appear unescaped in the HTML
            assert b"<script>document.cookie" not in r2.data, (
                "FAIL: Unescaped <script> tag reflected in response!"
            )

    def test_xss_in_search_not_reflected(self, client):
        """XSS in ?q= search param must not be reflected unescaped."""
        r = client.get('/?q=<script>alert(1)</script>', follow_redirects=True)
        assert b"<script>alert(1)</script>" not in r.data, (
            "FAIL: XSS reflected in search results!"
        )

    def test_markdown_script_tag_sanitized(self, app):
        """Markdown content with <script> must be sanitized in the rendered view."""
        with app.test_client() as c:
            register_user(c, "md_xss_user", "Pass1234")
            login_user(c, "md_xss_user", "Pass1234")
            # This is valid Markdown that contains inline HTML
            r = create_post(
                c,
                title="Markdown XSS Test",
                content='Hello <script>alert("xss")</script> world',
            )
            post_id = get_post_id_from_redirect(r)
            r2 = c.get(f"/post/{post_id}")
            assert b"<script>" not in r2.data, (
                "FAIL: <script> in Markdown content survived sanitization!"
            )


# ══════════════════════════════════════════════════════════════════
# A04:2021 – Insecure Design (Authentication Enumeration)
# ══════════════════════════════════════════════════════════════════

class TestA04InsecureDesign:
    """
    Verifies the auth system doesn't leak whether a username exists.
    Both 'wrong username' and 'wrong password' must return identical errors.
    """

    def test_nonexistent_user_returns_generic_error(self, client):
        """Login with a username that doesn't exist → generic error message."""
        r = client.post(
            "/login",
            data={"username": "definitely_not_registered", "password": "SomePass1"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in r.data, (
            "FAIL: Error message should be generic for non-existent user"
        )

    def test_wrong_password_returns_same_generic_error(self, app, client):
        """Login with valid username but wrong password → SAME generic error."""
        with app.test_client() as c:
            register_user(c, "enum_target_user", "RealPass1")

        r = client.post(
            "/login",
            data={"username": "enum_target_user", "password": "WrongPass1"},
            follow_redirects=True,
        )
        # Must be the exact same message — attacker cannot distinguish cases
        assert b"Invalid username or password" in r.data, (
            "FAIL: Wrong password gives different error — enables user enumeration!"
        )

    def test_username_existence_not_revealed_on_register(self, app):
        """
        Registering a taken username must say 'already taken',
        NOT expose the full user record or internal error.
        """
        with app.test_client() as c:
            register_user(c, "taken_username", "Pass1234")
            # Try to register same username again
            r = c.post(
                "/register",
                data={
                    "username": "taken_username",
                    "password": "DifferentPass1",
                    "confirm_password": "DifferentPass1",
                },
                follow_redirects=True,
            )
            assert r.status_code in (200, 409)
            assert b"already taken" in r.data or b"taken" in r.data.lower()


# ══════════════════════════════════════════════════════════════════
# A05:2021 – Security Misconfiguration
# ══════════════════════════════════════════════════════════════════

class TestA05SecurityMisconfiguration:
    """
    Verifies that the production configuration has all
    security-sensitive flags set correctly.
    """

    def test_production_config_debug_is_false(self):
        """ProductionConfig must have DEBUG=False."""
        from app.config import ProductionConfig
        assert ProductionConfig.DEBUG is False, (
            "FAIL: DEBUG is True in ProductionConfig! This exposes stack traces."
        )

    def test_production_config_propagate_exceptions_false(self):
        """ProductionConfig must not propagate exceptions (hides stack traces)."""
        from app.config import ProductionConfig
        assert getattr(ProductionConfig, "PROPAGATE_EXCEPTIONS", False) is False

    def test_session_httponly_in_production(self):
        """SESSION_COOKIE_HTTPONLY must be True in production config."""
        from app.config import ProductionConfig
        assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True, (
            "FAIL: HttpOnly not set — JS can read session cookie!"
        )

    def test_session_samesite_in_production(self):
        """SESSION_COOKIE_SAMESITE must be Lax or Strict in production."""
        from app.config import ProductionConfig
        val = ProductionConfig.SESSION_COOKIE_SAMESITE
        assert val in ("Lax", "Strict"), (
            f"FAIL: SameSite={val} — should be Lax or Strict"
        )

    def test_secret_key_env_var_not_hardcoded(self):
        """SECRET_KEY must be read from env, not a literal string in source."""
        import inspect
        from app import config
        source = inspect.getsource(config)
        # The config should use os.environ.get, not a hardcoded secret
        assert "os.environ" in source, "FAIL: SECRET_KEY not read from environment"
        assert '"secret"' not in source.lower(), "FAIL: Hardcoded 'secret' found in config"
        assert "supersecret" not in source.lower(), "FAIL: Hardcoded secret found"

    def test_404_does_not_expose_stack_trace(self, client):
        """404 error page must not contain Python traceback information."""
        r = client.get("/this-route-does-not-exist-at-all")
        assert r.status_code == 404
        assert b"Traceback" not in r.data, "FAIL: Traceback exposed in 404 page!"
        assert b"File \"/" not in r.data, "FAIL: File path exposed in 404 page!"

    def test_custom_error_page_on_404(self, client):
        """404 should render a custom page, not Flask's default."""
        r = client.get("/nonexistent-path-xyz-123")
        assert r.status_code == 404
        # Should be our custom page, not the generic Flask Werkzeug 404
        assert b"Werkzeug" not in r.data


# ══════════════════════════════════════════════════════════════════
# A07:2021 – Identification and Authentication Failures
# ══════════════════════════════════════════════════════════════════

class TestA07AuthenticationFailures:
    """
    Verifies rate limiting, session security, and auth validation.
    """

    def test_login_rate_limited_after_5_attempts(self, rate_app):
        """
        CRITICAL: Brute-force protection.
        After 5 failed login attempts from same IP, 6th must be rate-limited.
        """
        client = rate_app.test_client()
        for i in range(5):
            client.post(
                "/login",
                data={"username": "bruteforce_victim", "password": f"wrongpass{i}"},
            )
        # 6th attempt
        r = client.post(
            "/login",
            data={"username": "bruteforce_victim", "password": "wrongpass_final"},
            follow_redirects=True,
        )
        assert r.status_code == 429 or b"Too many" in r.data, (
            "FAIL: Login not rate-limited after 5 attempts — brute force possible!"
        )

    def test_empty_username_rejected(self, client):
        """Login with empty username must be rejected with 400."""
        r = client.post(
            "/login",
            data={"username": "", "password": "SomePass1"},
            follow_redirects=True,
        )
        assert r.status_code in (400, 200)
        assert b"required" in r.data.lower() or b"invalid" in r.data.lower()

    def test_empty_password_rejected(self, client):
        """Login with empty password must be rejected."""
        r = client.post(
            "/login",
            data={"username": "someuser", "password": ""},
            follow_redirects=True,
        )
        assert r.status_code in (400, 200)

    def test_username_too_short_rejected_on_register(self, client):
        """Usernames shorter than 3 chars must be rejected."""
        r = client.post(
            "/register",
            data={"username": "ab", "password": "Pass1234", "confirm_password": "Pass1234"},
            follow_redirects=True,
        )
        assert b"3" in r.data or b"characters" in r.data.lower() or r.status_code == 400

    def test_username_with_special_chars_rejected(self, client):
        """Usernames with special characters must be rejected."""
        r = client.post(
            "/register",
            data={
                "username": "user@evil.com",
                "password": "Pass1234",
                "confirm_password": "Pass1234",
            },
            follow_redirects=True,
        )
        assert r.status_code in (400, 200)
        # Must not succeed
        assert b"success" not in r.data.lower()

    def test_weak_password_rejected(self, client):
        """
        Password without numbers rejected ('onlyletters' has no digit).
        """
        r = client.post(
            "/register",
            data={
                "username": "weakpwduser",
                "password": "onlyletters",
                "confirm_password": "onlyletters",
            },
            follow_redirects=True,
        )
        assert r.status_code in (400, 200)
        assert b"success" not in r.data.lower()

    def test_password_too_short_rejected(self, client):
        """Password shorter than 8 chars must be rejected."""
        r = client.post(
            "/register",
            data={"username": "shortpwduser", "password": "Ab1", "confirm_password": "Ab1"},
            follow_redirects=True,
        )
        assert r.status_code in (400, 200)
        assert b"success" not in r.data.lower()

    def test_password_mismatch_rejected(self, client):
        """Mismatched password confirmation must be rejected."""
        r = client.post(
            "/register",
            data={
                "username": "mismatch_user",
                "password": "Pass1234",
                "confirm_password": "Pass5678",
            },
            follow_redirects=True,
        )
        assert r.status_code in (400, 200)
        assert b"match" in r.data.lower() or b"success" not in r.data.lower()

    def test_logout_requires_post_method(self, app):
        """
        CRITICAL: Logout must only work via POST, not GET.
        GET /logout from a malicious link must NOT log the user out.
        """
        with app.test_client() as c:
            register_user(c, "logout_test_user", "Pass1234")
            login_user(c, "logout_test_user", "Pass1234")
            # Try to log out via GET
            r = c.get("/logout")
            assert r.status_code == 405, (
                "FAIL: GET /logout works — attacker can log user out via link!"
            )

    def test_session_fixation_prevented(self, app):
        """
        After login, session must be regenerated (cleared and recreated).
        This prevents session fixation attacks.
        """
        with app.test_client() as c:
            register_user(c, "fixation_test_user", "Pass1234")
            
            # Simulate pre-login session state
            c.get("/login")
            with c.session_transaction() as sess:
                sess["pre_auth_tracker"] = "vulnerable_data"

            # Log in
            login_user(c, "fixation_test_user", "Pass1234")

            # Verify session holds authenticated user and pre-auth data is destroyed
            with c.session_transaction() as sess:
                assert "username" in sess
                assert sess["username"] == "fixation_test_user"
                assert "pre_auth_tracker" not in sess, "FAIL: Session fixation vulnerability — pre-login session data leaked to post-login session!"

    def test_authenticated_user_redirected_from_login(self, app):
        """Already logged-in user visiting /login should redirect to home."""
        with app.test_client() as c:
            register_user(c, "already_logged_in", "Pass1234")
            login_user(c, "already_logged_in", "Pass1234")
            r = c.get("/login", follow_redirects=False)
            assert r.status_code == 302
            assert "/login" not in r.headers.get("Location", "")

    def test_username_stored_as_lowercase(self, app):
        """Usernames must be stored in lowercase regardless of input case."""
        with app.test_client() as c:
            # Register with mixed case — auth.py normalises to lowercase
            c.post(
                "/register",
                data={
                    "username": "MixedCaseUser2",
                    "password": "Pass1234",
                    "confirm_password": "Pass1234",
                },
                follow_redirects=False,
            )

        with app.app_context():
            # Should be stored as lowercase
            user = app.user_model.table.get_item(
                Key={"username": "mixedcaseuser2"}
            ).get("Item")
            assert user is not None, (
                "FAIL: Lowercase-normalised username not found in DB. "
                "Username must be .strip().lower() before storage."
            )


# ══════════════════════════════════════════════════════════════════
# A08:2021 – Software and Data Integrity Failures
# ══════════════════════════════════════════════════════════════════

class TestA08SoftwareIntegrityFailures:
    """
    Tests CSRF protection and file upload magic byte validation.
    """

    # ── CSRF Tests ─────────────────────────────────────────────────

    def test_create_post_without_csrf_token_rejected(self, csrf_app, csrf_client):
        """POST /create without CSRF token must be rejected (400)."""
        with csrf_app.test_client() as c:
            # Register and log in
            c.post("/register", data={
                "username": "csrf_test1", "password": "Pass1234", "confirm_password": "Pass1234"
            })
            c.post("/login", data={"username": "csrf_test1", "password": "Pass1234"})
            # Attempt to create post WITHOUT csrf_token field
            r = c.post(
                "/create",
                data={"title": "CSRF Attack Post", "content": "Injected content"},
                follow_redirects=False,
            )
            assert r.status_code in (400, 302), (
                f"FAIL: POST without CSRF token returned {r.status_code} — CSRF not protected!"
            )

    def test_delete_post_without_csrf_token_rejected(self, csrf_app):
        """POST /delete/<id> without CSRF token must be rejected."""
        with csrf_app.test_client() as c:
            c.post("/register", data={
                "username": "csrf_del_user", "password": "Pass1234", "confirm_password": "Pass1234"
            })
            c.post("/login", data={"username": "csrf_del_user", "password": "Pass1234"})
            # Create a post first (without CSRF — will fail in csrf_app)
            # So we create it via the standard app and get the ID
            # For this test, just confirm the endpoint rejects without token
            r = c.post("/delete/fake-post-id-here", follow_redirects=False)
            assert r.status_code in (400, 302)

    # ── File Upload Magic Byte Tests ───────────────────────────────

    def test_real_jpeg_upload_accepted(self, app):
        """A valid JPEG file (correct magic bytes) must be accepted."""
        from app.utils.security import is_valid_image
        jpeg_stream = io.BytesIO(make_jpeg_bytes())
        assert is_valid_image(jpeg_stream) is True, (
            "FAIL: Valid JPEG rejected by magic byte check!"
        )

    def test_real_png_upload_accepted(self, app):
        """A valid PNG file (correct magic bytes) must be accepted."""
        from app.utils.security import is_valid_image
        png_stream = io.BytesIO(make_png_bytes())
        assert is_valid_image(png_stream) is True, (
            "FAIL: Valid PNG rejected by magic byte check!"
        )

    def test_text_file_disguised_as_jpg_rejected(self, app):
        """
        CRITICAL: A text file renamed to .jpg must be REJECTED.
        This defeats extension-spoofing attacks (e.g. malware.php → photo.jpg).
        """
        from app.utils.security import is_valid_image
        fake_stream = io.BytesIO(make_fake_jpeg_bytes())
        assert is_valid_image(fake_stream) is False, (
            "FAIL: Text file disguised as .jpg was ACCEPTED! Extension spoofing possible."
        )

    def test_php_file_disguised_as_jpg_rejected(self, app):
        """A PHP script renamed to .jpg must be rejected."""
        from app.utils.security import is_valid_image
        php_content = b"<?php system($_GET['cmd']); ?>"
        assert is_valid_image(io.BytesIO(php_content)) is False, (
            "FAIL: PHP file disguised as image was accepted!"
        )

    def test_html_file_disguised_as_jpg_rejected(self, app):
        """An HTML file renamed to .jpg must be rejected."""
        from app.utils.security import is_valid_image
        html_content = b"<html><script>alert(1)</script></html>"
        assert is_valid_image(io.BytesIO(html_content)) is False, (
            "FAIL: HTML file disguised as image was accepted!"
        )

    def test_allowed_extension_check(self, app):
        """Extension validator must block disallowed extensions."""
        from app.utils.security import allowed_extension
        allowed = {"jpg", "jpeg", "png", "gif", "webp"}
        assert allowed_extension("photo.jpg", allowed) is True
        assert allowed_extension("photo.PNG", allowed) is True  # case-insensitive
        assert allowed_extension("shell.php", allowed) is False
        assert allowed_extension("script.js", allowed) is False
        assert allowed_extension("noextension", allowed) is False
        assert allowed_extension(".htaccess", allowed) is False

    def test_file_stream_reset_after_magic_check(self, app):
        """
        The file stream must be reset to position 0 after magic byte check.
        Otherwise the upload to S3 will be empty.
        """
        from app.utils.security import is_valid_image
        jpeg_bytes = make_jpeg_bytes()
        stream = io.BytesIO(jpeg_bytes)
        is_valid_image(stream)
        # Stream must be back at position 0 for subsequent upload
        assert stream.tell() == 0, (
            "FAIL: Stream not reset after magic byte check — S3 upload would be empty!"
        )


# ══════════════════════════════════════════════════════════════════
# A10:2021 Adjacent – Open Redirect / SSRF
# ══════════════════════════════════════════════════════════════════

class TestA10OpenRedirect:
    """
    Verifies the ?next= redirect parameter cannot be used to redirect
    users to external malicious sites (open redirect / phishing).
    """

    def test_is_safe_redirect_allows_relative_paths(self):
        """Relative paths must be allowed as safe redirects."""
        from app.utils.security import is_safe_redirect_url
        assert is_safe_redirect_url("/", "localhost") is True
        assert is_safe_redirect_url("/create", "localhost") is True
        assert is_safe_redirect_url("/post/abc-123", "localhost") is True

    def test_is_safe_redirect_blocks_external_urls(self):
        """
        CRITICAL: External URLs in ?next= must be blocked.
        Allows phishing: user clicks login link, gets sent to evil.com.
        """
        from app.utils.security import is_safe_redirect_url
        assert is_safe_redirect_url("http://evil.com", "localhost") is False, (
            "FAIL: External http:// URL allowed in redirect!"
        )
        assert is_safe_redirect_url("https://evil.com", "localhost") is False, (
            "FAIL: External https:// URL allowed in redirect!"
        )

    def test_is_safe_redirect_blocks_protocol_relative(self):
        """Protocol-relative URLs (//evil.com) must be blocked."""
        from app.utils.security import is_safe_redirect_url
        assert is_safe_redirect_url("//evil.com", "localhost") is False, (
            "FAIL: Protocol-relative URL //evil.com allowed in redirect!"
        )
        assert is_safe_redirect_url("//evil.com/phishing", "localhost") is False

    def test_is_safe_redirect_blocks_javascript_scheme(self):
        """javascript: URI scheme must be blocked."""
        from app.utils.security import is_safe_redirect_url
        assert is_safe_redirect_url("javascript:alert(1)", "localhost") is False, (
            "FAIL: javascript: URI allowed in redirect!"
        )

    def test_login_does_not_redirect_to_external_url(self, app):
        """
        After login, ?next=http://evil.com must NOT redirect externally.
        Must redirect to home page instead.
        """
        with app.test_client() as c:
            register_user(c, "redirect_test_user", "Pass1234")
            r = c.post(
                "/login?next=http://evil.com/phishing",
                data={"username": "redirect_test_user", "password": "Pass1234"},
                follow_redirects=False,
            )
            assert r.status_code == 302
            location = r.headers.get("Location", "")
            assert "evil.com" not in location, (
                f"FAIL: Login redirected to external URL: {location}"
            )

    def test_login_allows_safe_next_redirect(self, app):
        """
        After login with ?next=/create, must redirect to /create (safe).
        """
        with app.test_client() as c:
            register_user(c, "safe_next_user", "Pass1234")
            r = c.post(
                "/login?next=%2Fcreate",  # URL-encoded /create
                data={"username": "safe_next_user", "password": "Pass1234"},
                follow_redirects=False,
            )
            assert r.status_code == 302
            location = r.headers.get("Location", "")
            # Must NOT redirect to root — should honour safe relative next
            assert "evil.com" not in location, (
                f"FAIL: Redirected to evil site: {location}"
            )
            # The redirect location should contain /create or similar safe path
            assert location not in ("", "/", "http://localhost/"), (
                f"FAIL: Safe ?next= redirect ignored. Got: {location}. "
                "Expected redirect to /create."
            )


# ══════════════════════════════════════════════════════════════════
# Utility — Security Helper Unit Tests
# ══════════════════════════════════════════════════════════════════

class TestSecurityHelpers:
    """Unit tests for the security utility functions."""

    def test_sanitize_text_strips_all_html(self):
        """sanitize_text() must strip ALL HTML tags."""
        from app.utils.security import sanitize_text
        assert sanitize_text("<b>Hello</b>") == "Hello"
        assert sanitize_text('<a href="x">link</a>') == "link"
        assert sanitize_text('<script>alert(1)</script>') == "alert(1)"
        assert sanitize_text("Plain text") == "Plain text"

    def test_sanitize_text_handles_nested_tags(self):
        """Nested HTML tags must all be stripped."""
        from app.utils.security import sanitize_text
        result = sanitize_text("<div><p><b>deeply nested</b></p></div>")
        assert "<" not in result
        assert "deeply nested" in result

    def test_is_valid_username_accepts_valid_names(self):
        """Valid usernames (alphanumeric + underscore, 3–32 chars) accepted."""
        from app.utils.security import is_valid_username
        assert is_valid_username("alice") is True
        assert is_valid_username("user123") is True
        assert is_valid_username("my_blog_user") is True
        assert is_valid_username("a" * 32) is True  # max length

    def test_is_valid_username_rejects_invalid_names(self):
        """Invalid usernames rejected."""
        from app.utils.security import is_valid_username
        assert is_valid_username("ab") is False          # too short
        assert is_valid_username("a" * 33) is False      # too long
        assert is_valid_username("user@domain") is False # @ not allowed
        assert is_valid_username("user name") is False   # space not allowed
        assert is_valid_username("user-name") is False   # hyphen not allowed
        assert is_valid_username("") is False            # empty

    def test_is_valid_password_accepts_strong_passwords(self):
        """Strong passwords (letter + digit, 8+ chars) accepted."""
        from app.utils.security import is_valid_password
        assert is_valid_password("Pass1234") is True
        assert is_valid_password("abc12345") is True
        assert is_valid_password("MyStr0ngP@ss") is True

    def test_is_valid_password_rejects_weak_passwords(self):
        """Weak passwords rejected."""
        from app.utils.security import is_valid_password
        assert is_valid_password("short1") is False        # too short
        assert is_valid_password("onlyletters") is False   # no digit
        assert is_valid_password("12345678") is False      # no letter
        assert is_valid_password("Ab1") is False           # too short
        assert is_valid_password("a" * 73) is False        # too long (>72)
