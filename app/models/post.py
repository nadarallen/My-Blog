"""
PostModel — DynamoDB data access for blog posts.

DynamoDB Table: myblog-posts
  PK: post_id (String, UUID4)

GSI: AuthorIndex
  PK: author (String)
  SK: created_at (String, ISO8601)
"""
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from boto3.dynamodb.conditions import Attr


class PostModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    # ──────────────────────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────────
    # READ & SEARCH
    # ──────────────────────────────────────────────────────────────

    def get_all_paginated(
        self,
        page: int,
        per_page: int,
        search: str = "",
        category: str = "",
        tag: str = "",
        author: str = "",
        status: str = "published",
        visibility: str = "public",
        include_all: bool = False,
    ) -> tuple[list[dict], int]:
        """
        Return a page of posts, filtered by search, category, tag, author, status, and visibility.
        """
        filter_exprs = []
        if not include_all:
            if status:
                filter_exprs.append(Attr("status").eq(status))
            if visibility:
                filter_exprs.append(Attr("visibility").eq(visibility))
        if category:
            filter_exprs.append(Attr("category_slug").eq(category))
        if author:
            filter_exprs.append(Attr("author").eq(author))
        if tag:
            filter_exprs.append(Attr("tags").contains(tag))

        if search:
            search_clean = search.strip().lower()
            filter_exprs.append(
                Attr("title_lower").contains(search_clean) | Attr("content_lower").contains(search_clean) | Attr("excerpt").contains(search_clean)
            )

        kwargs: dict = {}
        if filter_exprs:
            combined = filter_exprs[0]
            for expr in filter_exprs[1:]:
                combined = combined & expr
            kwargs["FilterExpression"] = combined

        posts: list[dict] = []
        while True:
            response = self.table.scan(**kwargs)
            posts.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)

        for post in posts:
            post["read_time"] = self._calc_read_time(post.get("content", ""))
            post["views"] = int(post.get("views", 0))
            post["likes_count"] = int(post.get("likes_count", 0))
            post["bookmarks_count"] = int(post.get("bookmarks_count", 0))
            post["comments_count"] = int(post.get("comments_count", 0))
            post.setdefault("status", "published")
            post.setdefault("visibility", "public")

        total = len(posts)
        start = (page - 1) * per_page
        return posts[start : start + per_page], total

    def get_by_id(self, post_id: str) -> Optional[dict]:
        """Fetch a post and atomically increment its view counter."""
        try:
            response = self.table.update_item(
                Key={"post_id": post_id},
                UpdateExpression="SET #v = if_not_exists(#v, :zero) + :inc",
                ExpressionAttributeNames={"#v": "views"},
                ExpressionAttributeValues={":inc": 1, ":zero": 0},
                ConditionExpression=Attr("post_id").exists(),
                ReturnValues="ALL_NEW",
            )
            post = response.get("Attributes")
            if post:
                self._format_post(post)
            return post
        except Exception:
            return self.get_by_id_no_increment(post_id)

    def get_by_id_no_increment(self, post_id: str) -> Optional[dict]:
        """Fetch a post WITHOUT incrementing view counter."""
        try:
            response = self.table.get_item(Key={"post_id": post_id})
            post = response.get("Item")
            if post:
                self._format_post(post)
            return post
        except Exception:
            return None

    def get_by_slug(self, slug: str) -> Optional[dict]:
        """Fetch a post by slug."""
        try:
            response = self.table.scan(
                FilterExpression=Attr("slug").eq(slug)
            )
            items = response.get("Items", [])
            if items:
                post = items[0]
                self._format_post(post)
                return post
            return None
        except Exception:
            return None

    def get_user_drafts(self, author: str) -> list[dict]:
        """Return all drafts for an author."""
        try:
            response = self.table.scan(
                FilterExpression=Attr("author").eq(author) & Attr("status").eq("draft")
            )
            items = response.get("Items", [])
            items.sort(key=lambda p: p.get("updated_at", p.get("created_at", "")), reverse=True)
            for p in items:
                self._format_post(p)
            return items
        except Exception:
            return []

    # ──────────────────────────────────────────────────────────────
    # WRITE & UPDATE
    # ──────────────────────────────────────────────────────────────

    def create(
        self,
        title: str,
        content: str,
        author: str,
        image_key: Optional[str] = None,
        subtitle: str = "",
        category_slug: str = "general",
        tags: Optional[list[str]] = None,
        status: str = "published",
        visibility: str = "public",
        scheduled_at: str = "",
        seo_title: str = "",
        seo_description: str = "",
        comments_enabled: bool = True,
    ) -> str:
        """Insert a new post. Returns post_id."""
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        slug = self._generate_slug(title, post_id)
        
        tags = [t.strip().lower() for t in (tags or []) if t.strip()]

        item = {
            "post_id": post_id,
            "title": title,
            "title_lower": title.lower(),
            "content": content,
            "content_lower": content.lower(),
            "excerpt": subtitle or content[:160].replace("\n", " ").strip(),
            "subtitle": subtitle,
            "slug": slug,
            "author": author,
            "image_key": image_key or "",
            "category_slug": category_slug or "general",
            "tags": tags,
            "status": status,
            "visibility": visibility,
            "scheduled_at": scheduled_at,
            "seo_title": seo_title or title,
            "seo_description": seo_description or subtitle or title,
            "comments_enabled": comments_enabled,
            "views": 0,
            "likes_count": 0,
            "bookmarks_count": 0,
            "comments_count": 0,
            "created_at": now,
            "updated_at": now,
            "versions": [{
                "version_id": 1,
                "title": title,
                "content": content,
                "created_at": now,
            }],
        }

        self.table.put_item(Item=item)
        return post_id

    def update(
        self,
        post_id: str,
        title: str,
        content: str,
        image_key: Optional[str] = None,
        subtitle: str = "",
        category_slug: str = "general",
        tags: Optional[list[str]] = None,
        status: str = "published",
        visibility: str = "public",
        scheduled_at: str = "",
        seo_title: str = "",
        seo_description: str = "",
        comments_enabled: bool = True,
    ) -> bool:
        """Update a post and store a revision in version history."""
        existing = self.get_by_id_no_increment(post_id)
        if not existing:
            return False

        now = datetime.now(timezone.utc).isoformat()
        versions = existing.get("versions", [])
        next_ver_id = len(versions) + 1
        versions.append({
            "version_id": next_ver_id,
            "title": title,
            "content": content,
            "created_at": now,
        })

        tags = [t.strip().lower() for t in (tags or []) if t.strip()]

        update_expr = (
            "SET title = :t, title_lower = :tl, content = :c, content_lower = :cl, "
            "subtitle = :st, excerpt = :ex, category_slug = :cat, tags = :tg, "
            "#stat = :s, visibility = :v, scheduled_at = :sch, seo_title = :stitle, "
            "seo_description = :sdesc, comments_enabled = :ce, updated_at = :u, versions = :ver"
        )
        expr_vals: dict = {
            ":t": title,
            ":tl": title.lower(),
            ":c": content,
            ":cl": content.lower(),
            ":st": subtitle,
            ":ex": subtitle or content[:160].replace("\n", " ").strip(),
            ":cat": category_slug,
            ":tg": tags,
            ":s": status,
            ":v": visibility,
            ":sch": scheduled_at,
            ":stitle": seo_title or title,
            ":sdesc": seo_description or subtitle or title,
            ":ce": comments_enabled,
            ":u": now,
            ":ver": versions,
        }

        if image_key is not None:
            update_expr += ", image_key = :i"
            expr_vals[":i"] = image_key

        try:
            self.table.update_item(
                Key={"post_id": post_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={"#stat": "status"},
                ExpressionAttributeValues=expr_vals,
                ConditionExpression=Attr("post_id").exists(),
            )
            return True
        except Exception:
            return False

    def delete(self, post_id: str) -> bool:
        """Soft-delete a post by setting status='deleted'."""
        try:
            self.table.update_item(
                Key={"post_id": post_id},
                UpdateExpression="SET #s = :s, updated_at = :u",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": "deleted",
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
            )
            return True
        except Exception:
            return False

    def publish_scheduled() -> int:
        """Find and publish any scheduled posts whose scheduled_at timestamp has passed."""
        now = datetime.now(timezone.utc).isoformat()
        published_count = 0
        try:
            response = self.table.scan(
                FilterExpression=Attr("status").eq("scheduled") & Attr("scheduled_at").lte(now)
            )
            for post in response.get("Items", []):
                self.table.update_item(
                    Key={"post_id": post["post_id"]},
                    UpdateExpression="SET #s = :s, updated_at = :u",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":s": "published", ":u": now},
                )
                published_count += 1
        except Exception:
            pass
        return published_count

    # ──────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────

    def _format_post(self, post: dict) -> None:
        post["read_time"] = self._calc_read_time(post.get("content", ""))
        post["views"] = int(post.get("views", 0))
        post["likes_count"] = int(post.get("likes_count", 0))
        post["bookmarks_count"] = int(post.get("bookmarks_count", 0))
        post["comments_count"] = int(post.get("comments_count", 0))
        post.setdefault("status", "published")
        post.setdefault("visibility", "public")
        post.setdefault("category_slug", "general")
        post.setdefault("tags", [])

    @staticmethod
    def _generate_slug(title: str, post_id: str) -> str:
        clean = "".join(c if c.isalnum() or c in (" ", "-") else "" for c in title.lower())
        slug_base = "-".join(clean.split())[:50]
        return f"{slug_base}-{post_id[:8]}" if slug_base else f"post-{post_id[:8]}"

    @staticmethod
    def _calc_read_time(content: str) -> int:
        """Estimate reading time based on ~200 words per minute."""
        word_count = len(content.split())
        return max(1, math.ceil(word_count / 200))

