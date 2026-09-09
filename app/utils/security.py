"""
Security utilities:
  - Magic byte file validation (defeats extension spoofing)
  - Input sanitization with bleach (defeats stored XSS)
  - Open redirect validator (defeats phishing via ?next= param)
  - Username format enforcer
"""
import re
from typing import Optional
from urllib.parse import urlparse

import bleach

# ──────────────────────────────────────────────────────────────────
# File Upload Security
# ──────────────────────────────────────────────────────────────────

# Real file signature bytes for allowed image types.
# These are checked against the ACTUAL file bytes, not the extension.
# An attacker cannot fake these by renaming files.
_IMAGE_MAGIC: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "jpeg"),          # JPEG/JPG
    (b"\x89PNG\r\n\x1a\n", "png"),      # PNG
    (b"GIF87a", "gif"),                 # GIF87
    (b"GIF89a", "gif"),                 # GIF89
    (b"RIFF", "webp"),                  # WebP (RIFF container — needs extra check)
]


def is_valid_image(file_stream) -> bool:
    """
    Validate that a file stream is a real image by checking magic bytes.

    This defeats extension-spoofing attacks where an attacker renames
    a malicious file (e.g., shell.php) to shell.jpg.

    The file stream is reset to position 0 after reading.
    """
    header = file_stream.read(12)
    file_stream.seek(0)  # Reset stream so it can be read again for upload

    for magic, fmt in _IMAGE_MAGIC:
        if header.startswith(magic):
            if fmt == "webp":
                # RIFF containers also include WAV/AVI — confirm it's WEBP
                return header[8:12] == b"WEBP"
            return True
    return False


def allowed_extension(filename: str, allowed: set) -> bool:
    """Check that the file extension is in the allowed set."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in allowed


# ──────────────────────────────────────────────────────────────────
# Input Sanitization (Stored XSS Prevention)
# ──────────────────────────────────────────────────────────────────

# Strip ALL HTML tags from user text fields (titles, plain text)
def sanitize_text(text: str) -> str:
    """
    Strip all HTML tags and attributes from a string.
    Used on title and other plain-text fields.

    Prevents stored XSS — even if Jinja's autoescaping ever fails,
    the data in the DB contains no HTML at all.
    """
    return bleach.clean(text, tags=[], attributes={}, strip=True).strip()


# Safe HTML tags allowed in RENDERED Markdown output
_SAFE_TAGS = [
    "p", "br", "strong", "em", "u", "s",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote",
    "code", "pre", "kbd",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "hr", "del",
]
_SAFE_ATTRS: dict = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "width", "height"],
    "*": ["class"],
}


def sanitize_rendered_markdown(html: str) -> str:
    """
    Sanitize HTML output from markdown2 to a safe allowlist.

    markdown2 converts user Markdown → HTML. We then pass that HTML
    through bleach to strip any injected <script> or dangerous tags,
    while keeping safe formatting tags intact.
    """
    cleaned = bleach.clean(html, tags=_SAFE_TAGS, attributes=_SAFE_ATTRS, strip=True)
    # Auto-linkify bare URLs in text — adds rel="nofollow noopener"
    return bleach.linkify(cleaned, callbacks=[bleach.callbacks.nofollow])


# ──────────────────────────────────────────────────────────────────
# Open Redirect Prevention
# ──────────────────────────────────────────────────────────────────

def is_safe_redirect_url(url: str, host: str) -> bool:
    """
    Validate that a redirect URL is safe (relative path or strictly same host).

    Prevents open redirect attacks via ?next=http://evil.com, protocol-relative
    bypasses (//evil.com, ///evil.com, /\\evil.com, \\\\evil.com), or CRLF injections.

    Allows:
        /home, /posts/123, /create, http://<host>/post/123
    Blocks:
        http://evil.com, //evil.com, ///evil.com, /\\evil.com, \\\\evil.com, javascript:alert(1)
    """
    if not url:
        return False

    url = url.strip()
    if any(c in url for c in ("\r", "\n", "\t")):
        return False

    # Reject protocol-relative and backslash evasion
    if url.startswith(("//", "/\\", "\\", "\\\\")):
        return False

    parsed = urlparse(url)

    # Relative URL case
    if not parsed.scheme and not parsed.netloc:
        return url.startswith("/") and not url.startswith("//")

    # Absolute URL case (e.g. from request.referrer)
    if parsed.scheme in ("http", "https"):
        clean_host = host.split(":")[0].lower() if host else ""
        clean_netloc = parsed.netloc.split(":")[0].lower()
        return bool(clean_host and clean_netloc == clean_host)

    return False


def is_valid_external_url(url: str) -> bool:
    """
    Validate that a URL uses strictly http:// or https:// with a valid network location.
    Rejects javascript:, data:, vbscript:, control characters, or relative links.
    Returns True if empty (optional field) or a valid HTTP/HTTPS URL.
    """
    if not url:
        return True
    url = url.strip()
    if any(c in url for c in ("\r", "\n", "\t", " ")):
        return False
    lower_url = url.lower()
    if lower_url.startswith(("javascript:", "data:", "vbscript:", "file:", "about:")):
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc:
        return False
    return True


# ──────────────────────────────────────────────────────────────────
# Username Validation
# ──────────────────────────────────────────────────────────────────

# Only lowercase letters, digits, underscores — 3 to 32 chars
_USERNAME_RE = re.compile(r"^[a-z0-9_]{3,32}$")

# At least 1 letter, 1 digit, 8–72 chars (72 = bcrypt/Argon2 practical max)
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,72}$")


def is_valid_username(username: str) -> bool:
    """Return True if username matches the allowed pattern."""
    return bool(_USERNAME_RE.match(username))


def is_valid_password(password: str) -> bool:
    """
    Return True if password meets minimum strength requirements:
      - 8–72 characters
      - At least one letter
      - At least one digit
    """
    return bool(_PASSWORD_RE.match(password))


# ──────────────────────────────────────────────────────────────────
# Security Tokens & Mentions
# ──────────────────────────────────────────────────────────────────

import secrets


def generate_secure_token(bytes_len: int = 32) -> str:
    """Generate a cryptographically secure random URL-safe token."""
    return secrets.token_urlsafe(bytes_len)


def parse_mentions(text: str) -> set[str]:
    """Extract valid @username mentions from post or comment text."""
    mentions = set(re.findall(r"@([a-z0-9_]{3,32})\b", text.lower()))
    return mentions

