"""
Admin routes: Complete Admin & Moderation Dashboard.
"""
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from app.utils.decorators import admin_required, moderator_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@moderator_required
def dashboard():
    users = current_app.user_model.list_users(limit=100)
    posts, total_posts = current_app.post_model.get_all_paginated(page=1, per_page=100, include_all=True)
    comments = current_app.comment_model.list_all(limit=100)
    reports = current_app.report_model.list_reports(status="pending")
    audit_logs = current_app.audit_model.list_logs(limit=20)

    total_views = sum(int(p.get("views", 0)) for p in posts)

    return render_template(
        "admin/dashboard.html",
        total_users=len(users),
        total_posts=total_posts,
        total_comments=len(comments),
        pending_reports=len(reports),
        total_views=total_views,
        recent_logs=audit_logs,
    )


@admin_bp.route("/users")
@admin_required
def manage_users():
    users = current_app.user_model.list_users(limit=200)
    return render_template("admin/users.html", users=users)


ALLOWED_ROLES = {"user", "moderator", "admin"}
ALLOWED_STATUSES = {"active", "suspended", "banned"}


@admin_bp.route("/users/role/<username>", methods=["POST"])
@admin_required
def update_user_role(username):
    role = request.form.get("role", "user").strip().lower()
    if role not in ALLOWED_ROLES:
        flash(f"Invalid role '{role}'. Allowed: {', '.join(sorted(ALLOWED_ROLES))}", "danger")
        return redirect(url_for("admin.manage_users"))

    current_app.user_model.update_role(username, role)
    current_app.audit_model.log_action(
        actor=session["username"],
        action="UPDATE_USER_ROLE",
        target=username,
        metadata={"new_role": role},
        ip_address=request.remote_addr or "",
    )
    flash(f"Updated role for {username} to {role}.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/status/<username>", methods=["POST"])
@moderator_required
def update_user_status(username):
    status = request.form.get("status", "active").strip().lower()
    if status not in ALLOWED_STATUSES:
        flash(f"Invalid status '{status}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}", "danger")
        return redirect(url_for("admin.manage_users"))

    current_app.user_model.update_status(username, status)
    current_app.audit_model.log_action(
        actor=session["username"],
        action="UPDATE_USER_STATUS",
        target=username,
        metadata={"new_status": status},
        ip_address=request.remote_addr or "",
    )
    flash(f"Updated status for {username} to {status}.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/posts")
@moderator_required
def manage_posts():
    posts, total = current_app.post_model.get_all_paginated(page=1, per_page=100, include_all=True)
    return render_template("admin/posts.html", posts=posts, total=total)


@admin_bp.route("/reports")
@moderator_required
def manage_reports():
    reports = current_app.report_model.list_reports()
    return render_template("admin/reports.html", reports=reports)


@admin_bp.route("/reports/resolve/<report_id>", methods=["POST"])
@moderator_required
def resolve_report(report_id):
    action = request.form.get("action", "resolved")
    notes = request.form.get("notes", "")
    current_app.report_model.resolve_report(
        report_id=report_id,
        status=action,
        moderator=session["username"],
        notes=notes,
    )
    current_app.audit_model.log_action(
        actor=session["username"],
        action="RESOLVE_REPORT",
        target=report_id,
        metadata={"action": action, "notes": notes},
        ip_address=request.remote_addr or "",
    )
    flash(f"Report {report_id[:8]} marked as {action}.", "success")
    return redirect(url_for("admin.manage_reports"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def manage_settings():
    if request.method == "POST":
        site_name = request.form.get("site_name", "My-Blog Platform")
        site_description = request.form.get("site_description", "")
        allow_reg = "allow_registration" in request.form
        allow_comm = "allow_comments" in request.form

        new_settings = {
            "site_name": site_name,
            "site_description": site_description,
            "allow_registration": allow_reg,
            "allow_comments": allow_comm,
        }
        current_app.settings_model.update_settings(new_settings)
        current_app.audit_model.log_action(
            actor=session["username"],
            action="UPDATE_SITE_SETTINGS",
            target="site_settings",
            metadata=new_settings,
            ip_address=request.remote_addr or "",
        )
        flash("Site settings updated successfully.", "success")
        return redirect(url_for("admin.manage_settings"))

    settings = current_app.settings_model.get_settings()
    return render_template("admin/settings.html", settings=settings)


@admin_bp.route("/audit")
@admin_required
def audit_logs():
    logs = current_app.audit_model.list_logs(limit=200)
    return render_template("admin/audit.html", logs=logs)
