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
