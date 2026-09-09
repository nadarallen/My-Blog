import html

from flask import Blueprint, current_app, Response, render_template, url_for

seo_bp = Blueprint("seo", __name__)


def _safe_xml(val) -> str:
    if not val:
        return ""
    return html.escape(html.unescape(str(val)), quote=True)


@seo_bp.route("/sitemap.xml")
def sitemap():
    posts, _ = current_app.post_model.get_all_paginated(page=1, per_page=500, status="published")
    categories = current_app.taxonomy_model.list_categories()
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    xml.append(f"  <url><loc>{url_for('posts.index', _external=True)}</loc><changefreq>daily</changefreq><priority>1.0</priority></url>")
    xml.append(f"  <url><loc>{url_for('search.search', _external=True)}</loc><changefreq>weekly</changefreq><priority>0.5</priority></url>")
    xml.append(f"  <url><loc>{url_for('seo.privacy_policy', _external=True)}</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>")
    xml.append(f"  <url><loc>{url_for('seo.terms_of_service', _external=True)}</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>")
    
    for cat in categories:
        xml.append(f"  <url><loc>{url_for('taxonomy.category_view', slug=cat['slug'], _external=True)}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>")
        
    for post in posts:
        xml.append(f"  <url><loc>{url_for('posts.view_post', post_id=post['post_id'], _external=True)}</loc><lastmod>{post.get('updated_at', post.get('created_at', ''))[:10]}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>")
        
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


@seo_bp.route("/robots.txt")
def robots():
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Sitemap: {url_for('seo.sitemap', _external=True)}
"""
    return Response(content, mimetype="text/plain")


@seo_bp.route("/privacy")
def privacy_policy():
    return render_template("privacy.html")


@seo_bp.route("/terms")
def terms_of_service():
    return render_template("terms.html")


@seo_bp.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("favicon.ico")


@seo_bp.route("/feed.xml")
def rss_feed():
    posts, _ = current_app.post_model.get_all_paginated(page=1, per_page=20, status="published")
    settings = current_app.settings_model.get_settings()
    
    site_title = _safe_xml(settings.get("site_name", "My-Blog"))
    site_desc = _safe_xml(settings.get("site_description", "Blog Feed"))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<rss version="2.0">')
    xml.append('  <channel>')
    xml.append(f'    <title>{site_title}</title>')
    xml.append(f'    <link>{url_for("posts.index", _external=True)}</link>')
    xml.append(f'    <description>{site_desc}</description>')
    xml.append('    <language>en-us</language>')
    
    for post in posts:
        title = _safe_xml(post.get("title", ""))
        excerpt = _safe_xml(post.get("excerpt", ""))
        author = _safe_xml(post.get("author", ""))
        created_at = _safe_xml(post.get("created_at", ""))
        guid = _safe_xml(post.get("post_id", ""))
        link = url_for("posts.view_post", post_id=post["post_id"], _external=True)

        xml.append('    <item>')
        xml.append(f'      <title>{title}</title>')
        xml.append(f'      <link>{link}</link>')
        xml.append(f'      <description>{excerpt}</description>')
        xml.append(f'      <author>{author}</author>')
        xml.append(f'      <pubDate>{created_at}</pubDate>')
        xml.append(f'      <guid>{guid}</guid>')
        xml.append('    </item>')
        
    xml.append('  </channel>')
    xml.append('</rss>')
    return Response("\n".join(xml), mimetype="application/xml")
