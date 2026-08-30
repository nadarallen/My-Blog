"""
NotificationModel — DynamoDB data access for user notifications.
"""
import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Attr


class NotificationModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    def create(
        self,
        recipient: str,
        actor: str,
        type_: str,
        target_id: str,
        message: str,
    ) -> str:
        """Create a new notification for a recipient user."""
        if recipient.lower() == actor.lower():
            return ""  # Don't notify self
        notification_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "notification_id": notification_id,
            "recipient": recipient.lower(),
            "actor": actor.lower(),
            "type": type_,
            "target_id": target_id,
            "message": message,
            "read": False,
            "created_at": now,
        }
        try:
            self.table.put_item(Item=item)
            return notification_id
        except Exception:
            return ""

    def get_user_notifications(self, recipient: str, limit: int = 50) -> list[dict]:
        """Fetch notifications for a recipient, sorted newest-first."""
        try:
            res = self.table.scan(
                FilterExpression=Attr("recipient").eq(recipient.lower())
            )
            items = res.get("Items", [])
            items.sort(key=lambda n: n.get("created_at", ""), reverse=True)
            return items[:limit]
        except Exception:
            return []

    def mark_all_read(self, recipient: str) -> bool:
        """Mark all unread notifications as read."""
        try:
            items = self.get_user_notifications(recipient, limit=100)
            for item in items:
                if not item.get("read"):
                    self.table.update_item(
                        Key={"notification_id": item["notification_id"]},
                        UpdateExpression="SET #r = :true",
                        ExpressionAttributeNames={"#r": "read"},
                        ExpressionAttributeValues={":true": True},
                    )
            return True
        except Exception:
            return False
