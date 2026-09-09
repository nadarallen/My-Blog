"""
Tests for RBAC roles, profile editing, 2FA, and user status management.
"""
from tests.conftest import register_user, login_user


def test_rbac_user_roles(client, app):
    register_user(client, username="author_user", password="Pass1234")
    login_user(client, username="author_user", password="Pass1234")

    # Regular user trying to access admin dashboard -> redirected
    res = client.get("/admin/", follow_redirects=True)
    assert b"Access denied" in res.data or res.status_code == 302


def test_profile_edit(client, app):
    register_user(client, username="profileuser", password="Pass1234")
    login_user(client, username="profileuser", password="Pass1234")

    res = client.post(
        "/profile/edit",
        data={
            "display_name": "Profile User Display",
            "bio": "Software Engineer & Blogger",
            "location": "San Francisco, CA",
            "website": "https://example.com",
            "avatar_url": "https://example.com/avatar.png",
            "cover_url": "",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Profile updated successfully" in res.data

    res_view = client.get("/author/profileuser")
    assert b"Profile User Display" in res_view.data
    assert b"Software Engineer" in res_view.data


def test_2fa_secret_storage(app):
    with app.app_context():
        app.user_model.create("tfauser", "Pass1234")
        ok = app.user_model.set_2fa_secret("tfauser", "JBSWY3DPEHPK3PXP")
        assert ok is True

        user = app.user_model.get_by_username("tfauser")
        assert user["two_factor_secret"] == "JBSWY3DPEHPK3PXP"
        assert user["two_factor_enabled"] is True


def test_moderator_cannot_modify_admin_status(client, app):
    with app.app_context():
        app.user_model.create("mod_user", "Pass1234", role="moderator")
        app.user_model.create("target_admin", "Pass1234", role="admin")

    login_user(client, username="mod_user", password="Pass1234")
    res = client.post(
        "/admin/users/status/target_admin",
        data={"status": "suspended"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Moderators cannot modify the status of administrator accounts" in res.data
    # Verify target_admin status is still active
    with app.app_context():
        target = app.user_model.get_by_username("target_admin")
        assert target["status"] == "active"


def test_admin_cannot_demote_self_or_primary_admin(client, app):
    with app.app_context():
        app.user_model.create("testadmin", "Pass1234", role="admin")
        app.user_model.create("second_admin", "Pass1234", role="admin")

    # Log in as second_admin
    login_user(client, username="second_admin", password="Pass1234")

    # Attempt to demote primary admin (testadmin)
    res1 = client.post(
        "/admin/users/role/testadmin",
        data={"role": "user"},
        follow_redirects=True,
    )
    assert b"Cannot demote the primary administrator account" in res1.data

    # Attempt to demote self (second_admin)
    res2 = client.post(
        "/admin/users/role/second_admin",
        data={"role": "user"},
        follow_redirects=True,
    )
    assert b"You cannot demote your own account from administrator" in res2.data


def test_role_change_invalidates_active_session(client, app):
    with app.app_context():
        app.user_model.create("victim_mod", "Pass1234", role="moderator")
        app.user_model.create("testadmin", "Pass1234", role="admin")

    # victim_mod logs in and gets session_version=1
    with client.session_transaction() as sess:
        sess["username"] = "victim_mod"
        sess["role"] = "moderator"
        sess["session_version"] = 1

    # Admin demotes victim_mod
    with app.app_context():
        app.user_model.update_role("victim_mod", "user")
        victim = app.user_model.get_by_username("victim_mod")
        assert victim["session_version"] == 2

    # victim_mod makes a request with their stale session -> session cleared / expired
    res = client.get("/admin/", follow_redirects=True)
    assert b"Your session has expired. Please sign in again" in res.data or b"Access denied" in res.data


def test_profile_edit_rejects_unsafe_urls(client, app):
    with app.app_context():
        app.user_model.create("xss_tester", "Pass1234")

    login_user(client, username="xss_tester", password="Pass1234")

    # Test javascript: URL scheme
    res = client.post(
        "/profile/edit",
        data={
            "display_name": "Tester",
            "bio": "Bio",
            "location": "Loc",
            "website": "javascript:alert(1)",
            "avatar_url": "",
            "cover_url": "",
        },
        follow_redirects=True,
    )
    assert res.status_code == 400
    assert b"Invalid URL format for Website" in res.data
