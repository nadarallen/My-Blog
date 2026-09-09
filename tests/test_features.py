"""
Tests for comments, social features (likes, bookmarks, follows), search, RSS feeds, and REST API endpoints.
"""
from tests.conftest import register_user, login_user, create_post, get_post_id_from_redirect


def test_comments_and_mentions(client, app):
    register_user(client, username="commenter", password="Pass1234")
    login_user(client, username="commenter", password="Pass1234")

    post_res = create_post(client, title="Post for Comments", content="Testing comment engine")
    post_id = get_post_id_from_redirect(post_res)

    res = client.post(
        f"/comments/add/{post_id}",
        data={"content": "Great article @commenter!"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Comment posted successfully" in res.data
    assert b"Great article" in res.data


def test_likes_and_bookmarks(client, app):
    register_user(client, username="liker", password="Pass1234")
    login_user(client, username="liker", password="Pass1234")

    post_res = create_post(client, title="Likable Post", content="Like me please")
    post_id = get_post_id_from_redirect(post_res)

    # Toggle like
    res_like = client.post(f"/like/{post_id}", follow_redirects=True)
    assert res_like.status_code == 200

    # Toggle bookmark
    res_bm = client.post(f"/bookmark/{post_id}", follow_redirects=True)
    assert res_bm.status_code == 200

    res_bms_page = client.get("/bookmarks")
    assert b"Likable Post" in res_bms_page.data


def test_search_and_rss_feeds(client, app):
    register_user(client, username="searcher", password="Pass1234")
    login_user(client, username="searcher", password="Pass1234")

    create_post(client, title="Unique Quantum Post", content="Quantum computing details")

    res_search = client.get("/search?q=Quantum")
    assert b"Unique Quantum Post" in res_search.data

    res_sitemap = client.get("/sitemap.xml")
    assert res_sitemap.status_code == 200
    assert "xml" in res_sitemap.content_type.lower()

    res_rss = client.get("/feed.xml")
    assert res_rss.status_code == 200
    assert b"rss" in res_rss.data.lower()


def test_api_v1_endpoints(client, app):
    register_user(client, username="apiuser", password="Pass1234")
    login_user(client, username="apiuser", password="Pass1234")

    create_post(client, title="API Test Post", content="Content for API test")

    res_list = client.get("/api/v1/posts")
    assert res_list.status_code == 200
    json_data = res_list.get_json()
    assert json_data["status"] == "success"
    assert len(json_data["results"]) > 0

    res_docs = client.get("/api/v1/docs")
    assert res_docs.status_code == 200
    assert b"REST API v1 Documentation" in res_docs.data


def test_privacy_and_terms_pages(client):
    res_priv = client.get("/privacy")
    assert res_priv.status_code == 200
    assert b"Privacy Policy" in res_priv.data
    assert b"Cookies &amp; Local Storage" in res_priv.data or b"Cookies" in res_priv.data

    res_terms = client.get("/terms")
    assert res_terms.status_code == 200
    assert b"Terms and Conditions" in res_terms.data
    assert b"Content Guidelines" in res_terms.data or b"Acceptance" in res_terms.data


def test_favicon_and_sitemap_legal_pages(client):
    res_fav = client.get("/favicon.ico")
    assert res_fav.status_code == 200

    res_sitemap = client.get("/sitemap.xml")
    assert res_sitemap.status_code == 200
    assert b"/privacy" in res_sitemap.data
    assert b"/terms" in res_sitemap.data

    res_robots = client.get("/robots.txt")
    assert res_robots.status_code == 200
    assert b"Sitemap:" in res_robots.data


def test_secrets_sanitized_from_template_globals(client, app):
    register_user(client, username="secretless_user", password="Pass1234")
    login_user(client, username="secretless_user", password="Pass1234")

    # Render a page while logged in and inspect response for leaked password hashes
    res = client.get("/")
    assert res.status_code == 200
    assert b"$argon2" not in res.data


def test_image_compression_resizing():
    import io
    from PIL import Image
    from app.utils.storage import compress_and_optimize_image

    # Create a 2400x1800 raw image
    raw_img = Image.new("RGB", (2400, 1800), color=(100, 150, 200))
    raw_buf = io.BytesIO()
    raw_img.save(raw_buf, format="JPEG", quality=100)
    raw_size = len(raw_buf.getvalue())

    raw_buf.seek(0)
    compressed_buf, ctype = compress_and_optimize_image(raw_buf, "jpg", max_width=1920, max_height=1080)
    compressed_size = len(compressed_buf.getvalue())

    assert ctype == "image/jpeg"
    assert compressed_size < raw_size

    # Verify dimensions resized within bounds
    compressed_buf.seek(0)
    out_img = Image.open(compressed_buf)
    assert out_img.width <= 1920
    assert out_img.height <= 1080


def test_custom_404_page(client):
    res = client.get("/nonexistent-page-xyz")
    assert res.status_code == 404
    assert b"Lost in the Ink" in res.data
    assert b"Back to Home" in res.data
    assert b"Explore Topics" in res.data


def test_registration_honeypot_spam_trap(client, app):
    res = client.post(
        "/register",
        data={
            "username": "bot_user",
            "password": "BotPassword123!",
            "confirm_password": "BotPassword123!",
            "hp_website": "http://spamsite.com",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    # Confirm bot_user was NOT actually created in DynamoDB
    user = app.user_model.get_by_username("bot_user")
    assert user is None


def test_comment_honeypot_spam_trap(client, app):
    register_user(client, username="honeypot_tester", password="Pass1234")
    login_user(client, username="honeypot_tester", password="Pass1234")
    post_res = create_post(client, title="Honeypot Post", content="Testing comment spam")
    post_id = get_post_id_from_redirect(post_res)

    res = client.post(
        f"/comments/add/{post_id}",
        data={
            "content": "Cheap pills online!",
            "hp_website": "http://spam-link.com",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    comments = app.comment_model.get_by_post(post_id)
    assert len(comments) == 0


def test_homepage_cta_and_category_links(client, app):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Get Started for Free" in res.data or b"Write a Story" in res.data


