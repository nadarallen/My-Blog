"""
Social routes: Likes, Bookmarks, Follows, Personalized Feed, and Notification Center.
"""
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from app.utils.decorators import login_required

social_bp = Blueprint("social", __name__)


@social_bp.route("/like/<post_id>", methods=["POST"])
@login_required
def toggle_like(post_id):
    username = session["username"]
    post = current_app.post_model.get_by_id_no_increment(post_id)
    if not post:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Post not found"}), 404
        flash("Post not found.", "danger")
        return redirect(url_for("posts.index"))

    liked = current_app.interaction_model.toggle_like(username, post_id)
    
    # Notify post author if liked
    if liked and post.get("author"):
        current_app.notification_model.create(
            recipient=post["author"],
            actor=username,
            type_="like",
            target_id=post_id,
            message=f"{username} liked your post '{post.get('title', '')}'",
        )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"liked": liked, "likes_count": int(post.get("likes_count", 0)) + (1 if liked else -1)})

    flash("Post liked!" if liked else "Post unliked.", "success")
    return redirect(request.referrer or url_for("posts.view_post", post_id=post_id))


@social_bp.route("/bookmark/<post_id>", methods=["POST"])
@login_required
def toggle_bookmark(post_id):
    username = session["username"]
    post = current_app.post_model.get_by_id_no_increment(post_id)
    if not post:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Post not found"}), 404
        flash("Post not found.", "danger")
        return redirect(url_for("posts.index"))

    bookmarked = current_app.interaction_model.toggle_bookmark(username, post_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"bookmarked": bookmarked})

    flash("Post saved to bookmarks!" if bookmarked else "Post removed from bookmarks.", "success")
    return redirect(request.referrer or url_for("posts.view_post", post_id=post_id))


@social_bp.route("/bookmarks")
@login_required
def bookmarks():
    username = session["username"]
    post_ids = current_app.interaction_model.get_user_bookmarks(username)
    posts = []
    for pid in post_ids:
        p = current_app.post_model.get_by_id_no_increment(pid)
        if p and p.get("status") == "published":
            posts.append(p)
    return render_template("bookmarks.html", posts=posts)


@social_bp.route("/follow/<author>", methods=["POST"])
@login_required
def toggle_follow(author):
    username = session["username"]
    if username.lower() == author.lower():
        flash("You cannot follow yourself.", "warning")
        return redirect(url_for("auth.author_profile", username=author))

    following = current_app.interaction_model.toggle_follow(username, author)
    if following:
        current_app.notification_model.create(
            recipient=author,
            actor=username,
            type_="follow",
            target_id=username,
            message=f"{username} started following you",
        )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"following": following})

    flash(f"You are now following {author}!" if following else f"Unfollowed {author}.", "info")
    return redirect(url_for("auth.author_profile", username=author))


@social_bp.route("/feed")
@login_required
def feed():
    username = session["username"]
    following_authors = current_app.interaction_model.get_following(username)
    all_posts, _ = current_app.post_model.get_all_paginated(page=1, per_page=50, status="published")
    
    feed_posts = [p for p in all_posts if p.get("author", "").lower() in following_authors]
    return render_template("feed.html", posts=feed_posts, following_count=len(following_authors))


@social_bp.route("/notifications")
@login_required
def notifications():
    username = session["username"]
    notifs = current_app.notification_model.get_user_notifications(username)
    current_app.notification_model.mark_all_read(username)
    return render_template("notifications.html", notifications=notifs)
