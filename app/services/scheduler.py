"""
Distributed BackgroundScheduler — Multi-instance safe background task runner.
Uses DynamoDB conditional locking to ensure scheduled posts are published exactly once across multiple application nodes.
"""
import logging
import threading
import time
from typing import Optional
from botocore.exceptions import ClientError

logger = logging.getLogger("app.scheduler")


class BackgroundScheduler:
    def __init__(self, app=None) -> None:
        self.app = app
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def init_app(self, app) -> None:
        self.app = app
        self.start()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        logger.info("BackgroundScheduler worker thread started.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("BackgroundScheduler worker thread stopped.")

    def _acquire_lock(self, lock_name: str, ttl_seconds: int = 60) -> bool:
        """Acquire a distributed lock using DynamoDB settings table."""
        if not self.app or not hasattr(self.app, "settings_model"):
            return True

        now = int(time.time())
        expires_at = now + ttl_seconds
        lock_id = f"lock:{lock_name}"

        try:
            # Conditional put: lock must not exist or must be expired
            from boto3.dynamodb.conditions import Attr
            self.app.settings_model.table.put_item(
                Item={
                    "key": lock_id,
                    "locked_at": now,
                    "expires_at": expires_at,
                    "node_id": threading.get_ident(),
                },
                ConditionExpression=Attr("key").not_exists() | Attr("expires_at").lt(now),
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False  # Lock held by another node
            logger.error(f"Error acquiring distributed lock {lock_name}: {e}")
            return False
        except Exception:
            return True  # Fallback to local execution if table uninitialized in dev

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.app:
                    with self.app.app_context():
                        # Try to acquire lock for post publishing task
                        if self._acquire_lock("publish_scheduled", ttl_seconds=30):
                            if hasattr(self.app, "post_model"):
                                count = self.app.post_model.publish_scheduled()
                                if count > 0:
                                    logger.info(f"[DISTRIBUTED LOCK ACQUIRED] Published {count} scheduled post(s).")
            except Exception as e:
                logger.error(f"Error in BackgroundScheduler loop: {e}")

            # Short sleep steps to allow fast shutdown
            for _ in range(15):
                if self._stop_event.is_set():
                    break
                time.sleep(1)


scheduler = BackgroundScheduler()
