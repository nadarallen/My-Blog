"""
InteractionModel — DynamoDB data access for likes, bookmarks, and author follows.
"""
from datetime import datetime, timezone
from typing import Optional
from boto3.dynamodb.conditions import Attr


class InteractionModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    def toggle_like(self, username: str, post_id: str) -> bool:
        """Toggle post like atomically. Returns True if liked, False if unliked."""
        key = f"like:{username}:{post_id}"
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.put_item(
                Item={
                    "interaction_id": key,
                    "type": "like",
                    "username": username,
                    "target_id": post_id,
                    "created_at": now,
                },
                ConditionExpression=Attr("interaction_id").not_exists(),
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            self.table.delete_item(Key={"interaction_id": key})
            return False
        except Exception:
            return False

    def has_liked(self, username: str, post_id: str) -> bool:
        """Check if user has liked a post."""
        key = f"like:{username}:{post_id}"
        try:
            res = self.table.get_item(Key={"interaction_id": key})
            return bool(res.get("Item"))
        except Exception:
            return False

    def toggle_bookmark(self, username: str, post_id: str) -> bool:
        """Toggle post bookmark atomically. Returns True if bookmarked, False if removed."""
        key = f"bookmark:{username}:{post_id}"
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.put_item(
                Item={
                    "interaction_id": key,
                    "type": "bookmark",
                    "username": username,
                    "target_id": post_id,
                    "created_at": now,
                },
                ConditionExpression=Attr("interaction_id").not_exists(),
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            self.table.delete_item(Key={"interaction_id": key})
            return False
        except Exception:
            return False

    def has_bookmarked(self, username: str, post_id: str) -> bool:
        """Check if user has bookmarked a post."""
        key = f"bookmark:{username}:{post_id}"
        try:
            res = self.table.get_item(Key={"interaction_id": key})
            return bool(res.get("Item"))
        except Exception:
            return False

    def get_user_bookmarks(self, username: str) -> list[str]:
        """Return list of post_ids bookmarked by user."""
        try:
            res = self.table.scan(
                FilterExpression=Attr("type").eq("bookmark") & Attr("username").eq(username)
            )
            return [item["target_id"] for item in res.get("Items", [])]
        except Exception:
            return []

    def toggle_follow(self, follower: str, author: str) -> bool:
        """Toggle following an author. Returns True if now following, False if unfollowed."""
        if follower.lower() == author.lower():
            return False
        key = f"follow:{follower.lower()}:{author.lower()}"
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.put_item(
                Item={
                    "interaction_id": key,
                    "type": "follow",
                    "username": follower.lower(),
                    "target_id": author.lower(),
                    "created_at": now,
                },
                ConditionExpression=Attr("interaction_id").not_exists(),
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            self.table.delete_item(Key={"interaction_id": key})
            return False
        except Exception:
            return False

    def is_following(self, follower: str, author: str) -> bool:
        """Check if follower follows author."""
        key = f"follow:{follower.lower()}:{author.lower()}"
        try:
            res = self.table.get_item(Key={"interaction_id": key})
            return bool(res.get("Item"))
        except Exception:
            return False

    def get_followers(self, author: str) -> list[str]:
        """List usernames following an author."""
        try:
            res = self.table.scan(
                FilterExpression=Attr("type").eq("follow") & Attr("target_id").eq(author.lower())
            )
            return [item["username"] for item in res.get("Items", [])]
        except Exception:
            return []

    def get_following(self, follower: str) -> list[str]:
        """List authors followed by follower."""
        try:
            res = self.table.scan(
                FilterExpression=Attr("type").eq("follow") & Attr("username").eq(follower.lower())
            )
            return [item["target_id"] for item in res.get("Items", [])]
        except Exception:
            return []
