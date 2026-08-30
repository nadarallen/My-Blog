"""
Comments routes: Post comments, nested replies, moderation, reports.
"""
from flask import Blueprint, current_app, flash, jsonify, redirect, request, session, url_for
from app.utils.decorators import login_required
from app.utils.security import parse_mentions, sanitize_text

comments_bp = Blueprint("comments", __name__)


@comments_bp.route("/comments/add/<post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id", "").strip()
    depth = int(request.form.get("depth", 0))

    if not content:
        flash("Comment content cannot be empty.", "warning")
        return redirect(request.referrer or url_for("posts.view_post", post_id=post_id))

    post = current_app.post_model.get_by_id_no_increment(post_id)
    if not post:
        flash("Post not found.", "danger")
        return redirect(url_for("posts.index"))

    author = session["username"]
    clean_content = sanitize_text(content)
    comment_id = current_app.comment_model.create(
        post_id=post_id,
        author=author,
        content=clean_content,
        parent_id=parent_id,
        depth=depth + 1 if parent_id else 0,
    )

    # Trigger notifications for post author
    if post.get("author") and post["author"] != author:
        current_app.notification_model.create(
            recipient=post["author"],
            actor=author,
            type_="comment",
            target_id=post_id,
            message=f"{author} commented on your post '{post.get('title', '')}'",
        )

    # Trigger notifications for @mentions
    mentions = parse_mentions(clean_content)
    for mentioned_user in mentions:
        if current_app.user_model.exists(mentioned_user):
            current_app.notification_model.create(
                recipient=mentioned_user,
                actor=author,
                type_="mention",
                target_id=post_id,
                message=f"{author} mentioned you in a comment on '{post.get('title', '')}'",
            )

    flash("Comment posted successfully!", "success")
    return redirect(url_for("posts.view_post", post_id=post_id) + f"#comment-{comment_id}")


@comments_bp.route("/comments/delete/<comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    username = session["username"]
    user_role = session.get("role", "user")
    comment = current_app.comment_model.get_by_id(comment_id)
    
    if not comment:
        flash("Comment not found.", "danger")
        return redirect(request.referrer or url_for("posts.index"))

    if comment.get("author") != username and user_role not in ("moderator", "admin"):
        flash("Unauthorized to delete this comment.", "danger")
        return redirect(request.referrer or url_for("posts.index"))

    current_app.comment_model.delete(comment_id)
    flash("Comment deleted.", "info")
    return redirect(request.referrer or url_for("posts.index"))


@comments_bp.route("/comments/report/<comment_id>", methods=["POST"])
@login_required
def report_comment(comment_id):
    reason = request.form.get("reason", "Spam or abuse").strip()
    username = session["username"]
    comment = current_app.comment_model.get_by_id(comment_id)
    if comment:
        current_app.report_model.create_report(
            reporter=username,
            target_type="comment",
            target_id=comment_id,
            reason=reason,
            details=f"Comment content: {comment.get('content', '')}",
        )
    flash("Comment reported to moderators. Thank you.", "info")
    return redirect(request.referrer or url_for("posts.index"))
