"""
Taxonomy routes: Categories and Tags browsing.
"""
from flask import Blueprint, current_app, render_template, request

taxonomy_bp = Blueprint("taxonomy", __name__)


@taxonomy_bp.route("/category/<slug>")
def category_view(slug):
    page = request.args.get("page", 1, type=int)
    category = current_app.taxonomy_model.get_category(slug)
    posts, total = current_app.post_model.get_all_paginated(
        page=page, per_page=6, category=slug, status="published"
    )
    total_pages = max(1, (total + 5) // 6)
    return render_template(
        "category.html",
        category=category,
        posts=posts,
        page=page,
        total_pages=total_pages,
        total_posts=total,
    )


@taxonomy_bp.route("/tag/<slug>")
def tag_view(slug):
    page = request.args.get("page", 1, type=int)
    posts, total = current_app.post_model.get_all_paginated(
        page=page, per_page=6, tag=slug, status="published"
    )
    total_pages = max(1, (total + 5) // 6)
    return render_template(
        "tag.html",
        tag_slug=slug,
        posts=posts,
        page=page,
        total_pages=total_pages,
        total_posts=total,
    )


@taxonomy_bp.route("/categories")
def list_categories():
    categories = current_app.taxonomy_model.list_categories()
    return render_template("categories_list.html", categories=categories)
