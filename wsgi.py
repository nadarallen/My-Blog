"""Gunicorn / production WSGI entry point.

Usage:
    gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

