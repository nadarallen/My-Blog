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

    def create(self, username: str, password: str) -> bool:
        """
        Create a new user. Username is always stored as lowercase.
        Returns False if the username already exists.

        Uses DynamoDB ConditionExpression to atomically prevent
        duplicate registration (no TOCTOU race condition).
        """
        username = username.strip().lower()
        try:
            self.table.put_item(
                Item={
                    "username": username,
                    "password_hash": _ph.hash(password),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                # Atomic uniqueness check — fails if username already exists
                ConditionExpression=Attr("username").not_exists(),
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return False  # Username taken
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────
    # AUTH
    # ──────────────────────────────────────────────────────────────

    def verify(self, username: str, password: str) -> bool:
        """
        Verify credentials. Always takes the same time whether the
        user exists or not — prevents user enumeration via timing.

        Returns True only if username exists AND password is correct.
        """
        username = username.strip().lower()
        response = self.table.get_item(Key={"username": username})
        user = response.get("Item")

        if not user:
            # Timing-safe: run the full Argon2 verification anyway
            # so the response time is identical to a wrong-password attempt
            try:
                _ph.verify(_DUMMY_HASH, password)
            except Exception:
                pass
            return False

        try:
            return _ph.verify(user["password_hash"], password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    # ──────────────────────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────────────────────

    def exists(self, username: str) -> bool:
        """Check if a username exists (case-insensitive)."""
        username = username.strip().lower()
        response = self.table.get_item(
            Key={"username": username},
            ProjectionExpression="username",  # Fetch only the key — minimize data transfer
        )
        return bool(response.get("Item"))
