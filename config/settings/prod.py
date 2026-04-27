"""Production settings.

Phase 3 (current): SQLite-based dev only — this file is a placeholder.
Phase 4 (planned): switch to PostgreSQL, tighten CORS, enable proper logging,
read all secrets from environment.
"""
from .base import *  # noqa: F401,F403

# TODO[Phase 4]: PostgreSQL configuration
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config("DB_NAME"),
#         "USER": config("DB_USER"),
#         "PASSWORD": config("DB_PASSWORD"),
#         "HOST": config("DB_HOST", default="localhost"),
#         "PORT": config("DB_PORT", default="5432"),
#     }
# }
