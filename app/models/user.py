"""
UserModel — DynamoDB data access for users with Argon2id hashing.

Security properties:
  - Argon2id: memory-hard, GPU-resistant (OWASP recommended over bcrypt/PBKDF2)
  - Timing-safe: always runs a dummy hash on failed user lookup
  - Usernames stored and compared as lowercase only
  - DynamoDB condition prevents overwriting existing users atomically
"""
from datetime import datetime, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from boto3.dynamodb.conditions import Attr

# Argon2id parameters — tuned to OWASP recommended minimums
# time_cost=2, memory_cost=64MB, parallelism=2
_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MiB RAM per hash — defeats GPU attacks
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

# Dummy hash used during timing-safe "user not found" path
_DUMMY_HASH = _ph.hash("__timing_safe_dummy__")


class UserModel:
    def __init__(self, dynamodb_resource, table_name: str) -> None:
        self.table = dynamodb_resource.Table(table_name)

    # ──────────────────────────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────────────────────────

    def create(
        self,
        username: str,
        password: str,
        email: str = "",
        role: str = "user",
        display_name: str = "",
    ) -> bool:
        """
        Create a new user. Username is always stored as lowercase.
        Returns False if the username already exists.
        """
        username = username.strip().lower()
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "username": username,
            "email": email.strip().lower(),
            "password_hash": _ph.hash(password),
            "role": role,
            "display_name": display_name or username,
            "avatar_url": "",
            "cover_url": "",
            "bio": "",
            "website": "",
            "location": "",
            "social_links": {},
            "two_factor_secret": "",
            "two_factor_enabled": False,
            "email_verified": False,
            "verification_token": "",
            "reset_token": "",
            "reset_token_expires": "",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr("username").not_exists(),
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────
    # AUTH & VERIFICATION
    # ──────────────────────────────────────────────────────────────

    def verify(self, username: str, password: str) -> bool:
        """Verify credentials in a timing-safe manner."""
        user = self.get_by_username(username)

        if not user or user.get("status") in ("suspended", "banned"):
            try:
                _ph.verify(_DUMMY_HASH, password)
            except Exception:
                pass
            return False

        try:
            return _ph.verify(user["password_hash"], password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def get_by_username(self, username: str) -> Optional[dict]:
        """Fetch user profile by username."""
        username = username.strip().lower()
        try:
            response = self.table.get_item(Key={"username": username})
            user = response.get("Item")
            if user:
                user.setdefault("role", "user")
                user.setdefault("status", "active")
                user.setdefault("display_name", username)
            return user
        except Exception:
            return None

    def exists(self, username: str) -> bool:
        """Check if a username exists (case-insensitive)."""
        return self.get_by_username(username) is not None

    def update_profile(self, username: str, data: dict) -> bool:
        """Update user profile attributes."""
        username = username.strip().lower()
        now = datetime.now(timezone.utc).isoformat()
        allowed = {
            "display_name",
            "bio",
            "website",
            "location",
            "avatar_url",
            "cover_url",
            "social_links",
        }
        update_attrs = {k: v for k, v in data.items() if k in allowed}
        if not update_attrs:
            return True

        update_expr_parts = []
        expr_vals = {":u": now}
        expr_names = {}

        for idx, (k, v) in enumerate(update_attrs.items()):
            param = f":val_{idx}"
            name_param = f"#field_{idx}"
            update_expr_parts.append(f"{name_param} = {param}")
            expr_vals[param] = v
            expr_names[name_param] = k

        update_expr = "SET " + ", ".join(update_expr_parts) + ", updated_at = :u"

        try:
            self.table.update_item(
                Key={"username": username},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_vals,
                ConditionExpression=Attr("username").exists(),
            )
            return True
        except Exception:
            return False

    def update_role(self, username: str, role: str) -> bool:
        """Update user RBAC role (user, author, moderator, admin)."""
        username = username.strip().lower()
        try:
            self.table.update_item(
                Key={"username": username},
                UpdateExpression="SET #r = :r, updated_at = :u",
                ExpressionAttributeNames={"#r": "role"},
                ExpressionAttributeValues={
                    ":r": role,
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
                ConditionExpression=Attr("username").exists(),
            )
            return True
        except Exception:
            return False

    def invalidate_sessions(self, username: str) -> bool:
        """Bump session_version to invalidate all existing sessions for this user."""
        username = username.strip().lower()
        try:
            self.table.update_item(
                Key={"username": username},
                UpdateExpression="ADD session_version :val SET updated_at = :u",
                ExpressionAttributeValues={
                    ":val": 1,
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
                ConditionExpression=Attr("username").exists(),
            )
            return True
        except Exception:
            return False

    def update_status(self, username: str, status: str) -> bool:
        """Update account status (active, suspended, banned) and invalidate sessions."""
        username = username.strip().lower()
        try:
            self.table.update_item(
                Key={"username": username},
                UpdateExpression="SET #s = :s, updated_at = :u ADD session_version :val",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": status,
                    ":u": datetime.now(timezone.utc).isoformat(),
                    ":val": 1,
                },
                ConditionExpression=Attr("username").exists(),
            )
            return True
        except Exception:
            return False

    def change_password(self, username: str, new_password: str) -> bool:
        """Change user password and invalidate all active sessions."""
        username = username.strip().lower()
        try:
            self.table.update_item(
                Key={"username": username},
                UpdateExpression="SET password_hash = :ph, updated_at = :u ADD session_version :val",
                ExpressionAttributeValues={
                    ":ph": _ph.hash(new_password),
                    ":u": datetime.now(timezone.utc).isoformat(),
                    ":val": 1,
                },
                ConditionExpression=Attr("username").exists(),
            )
            return True
        except Exception:
            return False

    def set_2fa_secret(self, username: str, secret: str) -> bool:
        """Set user TOTP secret."""
        username = username.strip().lower()
        try:
            self.table.update_item(
                Key={"username": username},
                UpdateExpression="SET two_factor_secret = :s, two_factor_enabled = :e",
                ExpressionAttributeValues={
                    ":s": secret,
                    ":e": bool(secret),
                },
                ConditionExpression=Attr("username").exists(),
            )
            return True
        except Exception:
            return False

    def delete_account(self, username: str) -> bool:
        """Delete user account."""
        username = username.strip().lower()
        try:
            self.table.delete_item(Key={"username": username})
            return True
        except Exception:
            return False

    def list_users(self, limit: int = 100) -> list[dict]:
        """Scan and return all users for administrative management."""
        try:
            response = self.table.scan(Limit=limit)
            users = response.get("Items", [])
            for u in users:
                u.pop("password_hash", None)
                u.pop("two_factor_secret", None)
                u.setdefault("role", "user")
                u.setdefault("status", "active")
                u.setdefault("session_version", 1)
            return users
        except Exception:
            return []
