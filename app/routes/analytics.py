"""
Analytics routes: Author dashboard analytics.
"""
from flask import Blueprint, current_app, render_template, session
from app.utils.decorators import login_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def dashboard():
    author = session["username"]
    posts, total_posts = current_app.post_model.get_all_paginated(
        page=1, per_page=100, author=author, include_all=True
    )

    total_views = sum(int(p.get("views", 0)) for p in posts)
    total_likes = sum(int(p.get("likes_count", 0)) for p in posts)
    total_bookmarks = sum(int(p.get("bookmarks_count", 0)) for p in posts)
    total_comments = sum(int(p.get("comments_count", 0)) for p in posts)
    followers = current_app.interaction_model.get_followers(author)

    top_posts = sorted(posts, key=lambda p: int(p.get("views", 0)), reverse=True)[:5]

    return render_template(
        "analytics.html",
        total_posts=total_posts,
        total_views=total_views,
        total_likes=total_likes,
        total_bookmarks=total_bookmarks,
        total_comments=total_comments,
        followers_count=len(followers),
        top_posts=top_posts,
        posts=posts,
    )
