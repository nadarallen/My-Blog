"""
AuditModel — Security audit trail logging for administrative and security actions.
"""
import uuid
from datetime import datetime, timezone


class AuditModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    def log_action(
        self,
        actor: str,
        action: str,
        target: str,
        metadata: dict = None,
        ip_address: str = "",
    ) -> str:
        """Record an immutable audit log entry."""
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "log_id": log_id,
            "actor": actor,
            "action": action,
            "target": target,
            "metadata": metadata or {},
            "ip_address": ip_address,
            "created_at": now,
        }
        try:
            self.table.put_item(Item=item)
            return log_id
        except Exception:
            return ""

    def list_logs(self, limit: int = 100) -> list[dict]:
        """Fetch audit log history, newest-first."""
        try:
            res = self.table.scan(Limit=limit)
            items = res.get("Items", [])
            items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return items
        except Exception:
            return []
