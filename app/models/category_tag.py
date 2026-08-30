"""
CategoryTagModel — Data access for blog categories and tags.
"""
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Attr

DEFAULT_CATEGORIES = [
    {"slug": "technology", "name": "Technology", "description": "Software, cloud architecture, security & AI"},
    {"slug": "engineering", "name": "Engineering", "description": "Backend development, systems engineering & design patterns"},
    {"slug": "security", "name": "Security", "description": "OWASP hardening, threat modeling & web security"},
    {"slug": "general", "name": "General", "description": "General articles, thoughts & updates"},
]


class CategoryTagModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        for cat in DEFAULT_CATEGORIES:
            self.create_category(cat["slug"], cat["name"], cat["description"])

    def create_category(self, slug: str, name: str, description: str = "", image_url: str = "") -> bool:
        slug = slug.strip().lower()
        key = f"cat:{slug}"
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.put_item(
                Item={
                    "item_id": key,
                    "type": "category",
                    "slug": slug,
                    "name": name,
                    "description": description,
                    "image_url": image_url,
                    "created_at": now,
                },
                ConditionExpression=Attr("item_id").not_exists(),
            )
            return True
        except Exception:
            return False

    def list_categories(self) -> list[dict]:
        try:
            res = self.table.scan(FilterExpression=Attr("type").eq("category"))
            cats = res.get("Items", [])
            cats.sort(key=lambda c: c.get("name", ""))
            return cats
        except Exception:
            return DEFAULT_CATEGORIES

    def get_category(self, slug: str) -> dict:
        key = f"cat:{slug.strip().lower()}"
        try:
            res = self.table.get_item(Key={"item_id": key})
            item = res.get("Item")
            if item:
                return item
        except Exception:
            pass
        return {"slug": slug, "name": slug.title(), "description": ""}

    def create_tag(self, name: str) -> str:
        slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
        key = f"tag:{slug}"
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.put_item(
                Item={
                    "item_id": key,
                    "type": "tag",
                    "slug": slug,
                    "name": name.strip(),
                    "created_at": now,
                },
                ConditionExpression=Attr("item_id").not_exists(),
            )
            return slug
        except Exception:
            return slug

    def list_tags(self) -> list[dict]:
        try:
            res = self.table.scan(FilterExpression=Attr("type").eq("tag"))
            tags = res.get("Items", [])
            tags.sort(key=lambda t: t.get("name", ""))
            return tags
        except Exception:
            return []
