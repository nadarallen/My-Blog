"""
ReportModel — Data access for user reports and moderation workflow.
"""
import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Attr


class ReportModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    def create_report(
        self,
        reporter: str,
        target_type: str,
        target_id: str,
        reason: str,
        details: str = "",
    ) -> str:
        """Create a new moderation report."""
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "report_id": report_id,
            "reporter": reporter,
            "target_type": target_type,  # 'post', 'comment', 'user'
            "target_id": target_id,
            "reason": reason,
            "details": details,
            "status": "pending",  # 'pending', 'reviewing', 'resolved', 'dismissed'
            "moderator_notes": "",
            "created_at": now,
            "updated_at": now,
        }
        try:
            self.table.put_item(Item=item)
            return report_id
        except Exception:
            return ""

    def list_reports(self, status: str = "") -> list[dict]:
        """Fetch reports for moderation queue."""
        try:
            kwargs = {}
            if status:
                kwargs["FilterExpression"] = Attr("status").eq(status)
            res = self.table.scan(**kwargs)
            items = res.get("Items", [])
            items.sort(key=lambda r: r.get("created_at", ""), reverse=True)
            return items
        except Exception:
            return []

    def resolve_report(
        self,
        report_id: str,
        status: str,
        moderator: str,
        notes: str = "",
    ) -> bool:
        """Update report status (resolved/dismissed) with moderator action notes."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.update_item(
                Key={"report_id": report_id},
                UpdateExpression="SET #s = :s, moderator = :m, moderator_notes = :n, updated_at = :u",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": status,
                    ":m": moderator,
                    ":n": notes,
                    ":u": now,
                },
            )
            return True
        except Exception:
            return False
