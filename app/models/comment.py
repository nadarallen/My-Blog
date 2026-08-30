"""
CommentModel — DynamoDB data access for comments and nested replies.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from boto3.dynamodb.conditions import Attr


class CommentModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    def create(
        self,
        post_id: str,
        author: str,
        content: str,
        parent_id: str = "",
        depth: int = 0,
    ) -> str:
        """Create a new comment or nested reply (max depth 3)."""
        comment_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "comment_id": comment_id,
            "post_id": post_id,
            "parent_id": parent_id,
            "depth": min(depth, 3),
            "author": author,
            "content": content,
            "likes_count": 0,
            "reports_count": 0,
            "status": "approved",
            "created_at": now,
            "updated_at": now,
        }
        self.table.put_item(Item=item)
        return comment_id

    def get_by_post(self, post_id: str, sort_by: str = "newest") -> list[dict]:
        """Fetch all approved comments for a post, structured for nested rendering."""
        try:
            response = self.table.scan(
                FilterExpression=Attr("post_id").eq(post_id) & Attr("status").eq("approved")
            )
            comments = response.get("Items", [])

            for c in comments:
                c["likes_count"] = int(c.get("likes_count", 0))
                c["depth"] = int(c.get("depth", 0))

            if sort_by == "oldest":
                comments.sort(key=lambda c: c.get("created_at", ""))
            elif sort_by == "top":
                comments.sort(key=lambda c: c.get("likes_count", 0), reverse=True)
            else:
                comments.sort(key=lambda c: c.get("created_at", ""), reverse=True)

            return comments
        except Exception:
            return []

    def get_by_id(self, comment_id: str) -> Optional[dict]:
        """Fetch comment by ID."""
        try:
            response = self.table.get_item(Key={"comment_id": comment_id})
            return response.get("Item")
        except Exception:
            return None

    def delete(self, comment_id: str) -> bool:
        """Soft-delete a comment."""
        try:
            self.table.update_item(
                Key={"comment_id": comment_id},
                UpdateExpression="SET #s = :s, content = :c, updated_at = :u",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": "deleted",
                    ":c": "[Comment deleted by user]",
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
            )
            return True
        except Exception:
            return False

    def list_all(self, limit: int = 100) -> list[dict]:
        """Scan all comments for admin/moderator dashboard."""
        try:
            response = self.table.scan(Limit=limit)
            return response.get("Items", [])
        except Exception:
            return []
