"""Development settings: PostgreSQL (since STEP 7.5), DEBUG=True, permissive CORS."""
from decouple import config

from .base import *  # noqa: F401,F403
from .base import BASE_DIR  # noqa: F401  (남겨둠 — SQLite fallback에서 참조)

DEBUG = True
ALLOWED_HOSTS = ["*"]

# === STEP 7.5: SQLite -> PostgreSQL 전환 ===
# 백업: backups/db.sqlite3.before-pg
# 이전 SQLite 설정 (롤백용 보존):
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DB_NAME", default="munbeop"),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default=""),
        "PORT": config("DB_PORT", default="5432"),
    }
}

CORS_ALLOW_ALL_ORIGINS = True
