"""Gunicorn / production WSGI entry point.

Usage:
    gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
"""
import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))
