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

    def get_all_paginated(
        self, page: int, per_page: int, search: str = ""
    ) -> tuple[list[dict], int]:
        """
        Return a page of posts, optionally filtered by search term.
        DynamoDB Scan is used here (suitable for small–medium datasets).
        For large datasets, consider Elasticsearch or OpenSearch.
        """
        kwargs: dict = {}
        if search:
            kwargs["FilterExpression"] = (
                Attr("title").contains(search) | Attr("content").contains(search)
            )

        # Collect all matching items (DynamoDB paginates internally)
        posts: list[dict] = []
        while True:
            response = self.table.scan(**kwargs)
            posts.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        # Sort newest-first in Python (DynamoDB Scan has no ORDER BY)
        posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)

        # Annotate with computed fields
        for post in posts:
            post["read_time"] = self._calc_read_time(post.get("content", ""))
            # DynamoDB returns Decimals for numbers; convert to int
            post["views"] = int(post.get("views", 0))

        total = len(posts)
        start = (page - 1) * per_page
        return posts[start : start + per_page], total

    def get_by_id(self, post_id: str) -> Optional[dict]:
        """
        Fetch a post and atomically increment its view counter.
        Returns None if the post doesn't exist.
        """
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
                post["read_time"] = self._calc_read_time(post.get("content", ""))
                post["views"] = int(post.get("views", 0))
            return post
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return None
        except Exception:
            return None

    def get_by_id_no_increment(self, post_id: str) -> Optional[dict]:
        """
        Fetch a post WITHOUT incrementing view counter.
        Used for edit/delete operations.
        """
        try:
            response = self.table.get_item(Key={"post_id": post_id})
            return response.get("Item")
        except Exception:
            return None

    # ──────────────────────────────────────────────────────────────
    # WRITE
    # ──────────────────────────────────────────────────────────────

    def create(
        self,
        title: str,
        content: str,
        author: str,
        image_key: Optional[str] = None,
    ) -> str:
        """Insert a new post. Returns the new post_id."""
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "post_id": post_id,
            "title": title,
            "content": content,
            "author": author,
            "created_at": now,
            "views": 0,
        }
        if image_key:
            item["image_key"] = image_key

        self.table.put_item(Item=item)
        return post_id

    def update(
        self,
        post_id: str,
        title: str,
        content: str,
        image_key: Optional[str] = None,
    ) -> bool:
        """Update title, content, and optionally the image key."""
        try:
            update_expr = "SET title = :t, content = :c, updated_at = :u"
            expr_vals: dict = {
                ":t": title,
                ":c": content,
                ":u": datetime.now(timezone.utc).isoformat(),
            }
            if image_key is not None:
                update_expr += ", image_key = :i"
                expr_vals[":i"] = image_key

            self.table.update_item(
                Key={"post_id": post_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_vals,
                ConditionExpression=Attr("post_id").exists(),
            )
            return True
        except Exception:
            return False

    def delete(self, post_id: str) -> bool:
        """Delete a post by ID."""
        try:
            self.table.delete_item(Key={"post_id": post_id})
            return True
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _calc_read_time(content: str) -> int:
        """Estimate reading time based on ~200 words per minute."""
        word_count = len(content.split())
        return max(1, math.ceil(word_count / 200))
