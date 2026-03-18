"""
Configuration de l'application Flask.
La SECRET_KEY doit être changée en production.
"""
import os
import secrets


def _load_mailapi_settings(file_path="MailAPI.txt"):
    """Charge les paramètres SMTP depuis un fichier key=value."""
    settings = {}
    if not os.path.exists(file_path):
        return settings

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            settings[key.strip()] = value.strip()
    return settings


_MAILAPI = _load_mailapi_settings()


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # En production, passer à True si HTTPS
    SESSION_COOKIE_SECURE = False

    MAILTRAP_SMTP_HOST = _MAILAPI.get("MAILTRAP_SMTP_HOST")
    MAILTRAP_SMTP_PORT = int(_MAILAPI.get("MAILTRAP_SMTP_PORT", "587"))
    MAILTRAP_SMTP_USERNAME = _MAILAPI.get("MAILTRAP_SMTP_USERNAME")
    MAILTRAP_SMTP_PASSWORD = _MAILAPI.get("MAILTRAP_SMTP_PASSWORD")
    MAILTRAP_SMTP_USE_TLS = _MAILAPI.get("MAILTRAP_SMTP_USE_TLS", "True").lower() == "true"

    MAILTRAP_FROM_NAME = _MAILAPI.get("MAILTRAP_FROM_NAME", "AppDec VideoGame")
    MAILTRAP_FROM_EMAIL = _MAILAPI.get("MAILTRAP_FROM_EMAIL")
