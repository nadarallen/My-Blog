"""
Search & Discovery routes: Full-text search, filtering, and recommendations.
"""
from flask import Blueprint, current_app, render_template, request

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    tag = request.args.get("tag", "").strip()
    author = request.args.get("author", "").strip()
    page = request.args.get("page", 1, type=int)

    posts, total = current_app.post_model.get_all_paginated(
        page=page,
        per_page=6,
        search=query,
        category=category,
        tag=tag,
        author=author,
        status="published",
    )

    categories = current_app.taxonomy_model.list_categories()
    total_pages = max(1, (total + 5) // 6)

    return render_template(
        "search.html",
        query=query,
        category=category,
        tag=tag,
        author=author,
        posts=posts,
        page=page,
        total_pages=total_pages,
        total_results=total,
        categories=categories,
    )
