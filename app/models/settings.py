"""
SettingsModel — Site configuration, registration toggles, and feature flags.
"""
from datetime import datetime, timezone

DEFAULT_SETTINGS = {
    "key": "site_settings",
    "site_name": "My-Blog Platform",
    "site_description": "Cloud-Native Enterprise-Grade Blogging Platform",
    "allow_registration": True,
    "allow_comments": True,
    "require_email_verification": False,
    "feature_flags": {
        "enable_2fa": True,
        "enable_rich_editor": True,
        "enable_analytics": True,
        "enable_rss": True,
    },
}


class SettingsModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        try:
            self.table.put_item(
                Item=DEFAULT_SETTINGS,
                ConditionExpression="attribute_not_exists(#k)",
                ExpressionAttributeNames={"#k": "key"},
            )
        except Exception:
            pass

    def get_settings(self) -> dict:
        try:
            res = self.table.get_item(Key={"key": "site_settings"})
            item = res.get("Item")
            if item:
                return item
        except Exception:
            pass
        return DEFAULT_SETTINGS

    def update_settings(self, data: dict) -> bool:
        item = self.get_settings()
        item.update(data)
        item["key"] = "site_settings"
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            self.table.put_item(Item=item)
            return True
        except Exception:
            return False
