"""Flask extension singletons — initialized in create_app()."""
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# CSRF protection — applied globally to all POST/PUT/DELETE requests
csrf = CSRFProtect()

# Rate limiter — keyed by real client IP
# Default limits applied globally; per-route limits override these
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://",
)
