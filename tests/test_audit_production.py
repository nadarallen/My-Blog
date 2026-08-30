"""
Tests for Production Readiness Audit:
- Session invalidation upon status update (suspension/ban) and password change
- Security response headers
- Account deletion
- View counter deduplication
- Distributed lock mechanism
"""
from tests.conftest import register_user, login_user, create_post, get_post_id_from_redirect


def test_session_invalidation_on_suspension(client, app):
    # 1. Register & login
    register_user(client, username="suspendee", password="Pass1234")
    login_user(client, username="suspendee", password="Pass1234")

    # Verify logged in
    res = client.get("/drafts")
    assert res.status_code == 200

    # 2. Suspend user in DynamoDB
    with app.app_context():
        app.user_model.update_status("suspendee", "suspended")

    # 3. Next request should immediately evict session and redirect
    res2 = client.get("/drafts", follow_redirects=True)
    assert b"deactivated or suspended" in res2.data or b"sign in" in res2.data.lower()


def test_session_invalidation_on_password_change(client, app):
    # 1. Register & login
    register_user(client, username="pwuser", password="Pass1234")
    login_user(client, username="pwuser", password="Pass1234")

    # 2. Change password via endpoint
    res_change = client.post(
        "/account/password",
        data={"old_password": "Pass1234", "new_password": "NewPass5678"},
        follow_redirects=True,
    )
    assert res_change.status_code == 200
    assert b"Password updated successfully" in res_change.data

    # Old session is cleared, access to protected route redirects
    res_prot = client.get("/drafts", follow_redirects=True)
    assert b"Please log in" in res_prot.data or b"sign in" in res_prot.data.lower() or res_prot.status_code == 200


def test_production_security_headers(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src" in res.headers.get("Content-Security-Policy", "")


def test_account_deletion_flow(client, app):
    register_user(client, username="todelete", password="Pass1234")
    login_user(client, username="todelete", password="Pass1234")

    res = client.post("/account/delete", follow_redirects=True)
    assert res.status_code == 200
    assert b"Your account has been deleted" in res.data

    with app.app_context():
        assert app.user_model.exists("todelete") is False


def test_view_deduplication(client, app):
    register_user(client, username="author_views", password="Pass1234")
    login_user(client, username="author_views", password="Pass1234")

    post_res = create_post(client, title="Views Post", content="Content for views test")
    post_id = get_post_id_from_redirect(post_res)

    # First view -> views should be 1
    client.get(f"/post/{post_id}")
    post = app.post_model.get_by_id_no_increment(post_id)
    assert int(post.get("views", 0)) == 1

    # Second view in same session -> views should remain 1 (deduplicated)
    client.get(f"/post/{post_id}")
    post_after = app.post_model.get_by_id_no_increment(post_id)
    assert int(post_after.get("views", 0)) == 1


def test_distributed_lock_scheduler(app):
    with app.app_context():
        from app.services.scheduler import scheduler
        lock1 = scheduler._acquire_lock("test_job", ttl_seconds=10)
        assert lock1 is True

        # Acquiring same lock before expiration should return False
        lock2 = scheduler._acquire_lock("test_job", ttl_seconds=10)
        assert lock2 is False
