"""
SEO and RSS routes: sitemap.xml, robots.txt, and RSS/Atom feeds.
"""
from flask import Blueprint, current_app, Response, render_template, url_for

seo_bp = Blueprint("seo", __name__)


@seo_bp.route("/sitemap.xml")
def sitemap():
    posts, _ = current_app.post_model.get_all_paginated(page=1, per_page=500, status="published")
    categories = current_app.taxonomy_model.list_categories()
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    xml.append(f"  <url><loc>{url_for('posts.index', _external=True)}</loc><changefreq>daily</changefreq><priority>1.0</priority></url>")
    xml.append(f"  <url><loc>{url_for('search.search', _external=True)}</loc><changefreq>weekly</changefreq><priority>0.5</priority></url>")
    
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


@seo_bp.route("/feed.xml")
def rss_feed():
    posts, _ = current_app.post_model.get_all_paginated(page=1, per_page=20, status="published")
    settings = current_app.settings_model.get_settings()
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<rss version="2.0">')
    xml.append('  <channel>')
    xml.append(f'    <title>{settings.get("site_name", "My-Blog")}</title>')
    xml.append(f'    <link>{url_for("posts.index", _external=True)}</link>')
    xml.append(f'    <description>{settings.get("site_description", "Blog Feed")}</description>')
    xml.append('    <language>en-us</language>')
    
    for post in posts:
        xml.append('    <item>')
        xml.append(f'      <title>{post.get("title", "")}</title>')
        xml.append(f'      <link>{url_for("posts.view_post", post_id=post["post_id"], _external=True)}</link>')
        xml.append(f'      <description>{post.get("excerpt", "")}</description>')
        xml.append(f'      <author>{post.get("author", "")}</author>')
        xml.append(f'      <pubDate>{post.get("created_at", "")}</pubDate>')
        xml.append(f'      <guid>{post["post_id"]}</guid>')
        xml.append('    </item>')
        
    xml.append('  </channel>')
    xml.append('</rss>')
    return Response("\n".join(xml), mimetype="application/xml")
