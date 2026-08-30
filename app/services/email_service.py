"""
EmailService — Asynchronous email delivery service for verification, password resets, and alerts.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("app.email")
_executor = ThreadPoolExecutor(max_workers=3)


def send_email_async(to_email: str, subject: str, body: str) -> None:
    """Queue an email for background delivery without blocking HTTP request execution."""
    _executor.submit(_send_email_task, to_email, subject, body)


def _send_email_task(to_email: str, subject: str, body: str) -> None:
    try:
        # Production SMTP or AWS SES integration point
        logger.info(f"[EMAIL DISPATCH] To: {to_email} | Subject: '{subject}' | Length: {len(body)} chars")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
