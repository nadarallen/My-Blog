"""
Backwards-compatibility shim.

The monolithic app.py has been replaced with the `app/` package
using the Blueprint application factory pattern.

Production entry point: wsgi.py (used by Gunicorn/Docker)
Development entry point: flask --app wsgi run
"""
from wsgi import app  # noqa: F401  re-exported for `flask run`

if __name__ == "__main__":
    # Direct execution: python app.py (development only)
    # Production uses: gunicorn wsgi:app
    import os
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
