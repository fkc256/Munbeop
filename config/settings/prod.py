"""Production settings.

Phase 3 (current): basic security headers + DEBUG=False; DB는 base.py의
SQLite를 그대로 사용 (실배포는 4차에서 PostgreSQL 전환).

Phase 4 (planned): switch to PostgreSQL, tighten CORS, enable proper
logging, read all secrets from environment, configure cache/celery.
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# 4차에서 실제 도메인으로 좁힘 — 지금은 환경변수 그대로 사용 (.env에서 지정)
# ALLOWED_HOSTS는 base.py의 decouple 처리로 .env에서 읽음

# 보안 헤더
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# CORS는 운영 도메인만 허용 (4차에서 실제 도메인 추가)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS: list[str] = []

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
