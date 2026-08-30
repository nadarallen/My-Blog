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
