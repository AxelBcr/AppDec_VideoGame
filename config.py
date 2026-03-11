"""
Configuration de l'application Flask.
La SECRET_KEY doit être changée en production.
"""
import os
import secrets


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # En production, passer à True si HTTPS
    SESSION_COOKIE_SECURE = False
