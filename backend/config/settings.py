import os
import ssl
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv, dotenv_values

from config.redis_url import ensure_rediss_ssl_cert_reqs

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _normalize_anthropic_key(raw: str) -> str:
    return (raw or '').strip().strip('`\'"').replace('\r', '')


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.meetings',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database: PostgreSQL in production (DATABASE_URL); SQLite for local dev
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=int(os.getenv('DATABASE_CONN_MAX_AGE', '600')),
            conn_health_checks=True,
        ),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

GS_MEDIA_BUCKET = os.getenv('GS_MEDIA_BUCKET', '').strip()
if GS_MEDIA_BUCKET:
    GS_BUCKET_NAME = GS_MEDIA_BUCKET
    STORAGES = {
        'default': {'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
    }
    GS_DEFAULT_ACL = None
    GS_QUERYSTRING_AUTH = True
    _gs_project = os.getenv('GCP_PROJECT_ID', os.getenv('GOOGLE_CLOUD_PROJECT', '')).strip()
    if _gs_project:
        GS_PROJECT_ID = _gs_project
else:
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF — JWT for SPA (no cookie CSRF on API routes)
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', '14'))),
    'ROTATE_REFRESH_TOKENS': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS
CORS_ALLOWED_ORIGINS = [
    x.strip()
    for x in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if x.strip()
]
CORS_ALLOW_ALL_ORIGINS = DEBUG

CSRF_TRUSTED_ORIGINS = [
    x.strip()
    for x in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if x.strip()
]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Celery
_celery_broker_raw = os.getenv('CELERY_BROKER_URL', '').strip()
_celery_result_raw = os.getenv('CELERY_RESULT_BACKEND', '').strip()
CELERY_BROKER_URL = ensure_rediss_ssl_cert_reqs(
    _celery_broker_raw or 'redis://localhost:6379/0'
)
CELERY_RESULT_BACKEND = ensure_rediss_ssl_cert_reqs(
    _celery_result_raw or 'redis://localhost:6379/0'
)
# Some Celery/kombu paths read broker/result URLs from os.environ (Cloud Run injects raw rediss://).
os.environ['CELERY_BROKER_URL'] = CELERY_BROKER_URL
os.environ['CELERY_RESULT_BACKEND'] = CELERY_RESULT_BACKEND

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour max per task
# Local dev without a worker: CELERY_TASK_ALWAYS_EAGER=True (runs tasks in-process; use only for dev)
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False') == 'True'
CELERY_TASK_EAGER_PROPAGATES = True

# Postgres-backed deploys need a real Redis — otherwise Cloud Run can boot an old SQLite revision and Celery silently targets localhost.
if DATABASE_URL and not CELERY_TASK_ALWAYS_EAGER:
    if not _celery_broker_raw or not _celery_result_raw:
        raise ImproperlyConfigured(
            'DATABASE_URL is set but CELERY_BROKER_URL and CELERY_RESULT_BACKEND are missing '
            '(set both to your hosted Redis URLs, e.g. Upstash rediss://...) or use '
            'CELERY_TASK_ALWAYS_EAGER=True only for debugging.'
        )

# Extra TLS hints for rediss (kombu/redis-py; complements query param above).
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': ssl.CERT_REQUIRED}
if CELERY_RESULT_BACKEND.startswith('rediss://'):
    CELERY_REDIS_BACKEND_USE_SSL = {'ssl_cert_reqs': ssl.CERT_REQUIRED}

# Upstash free-tier drops idle TLS connections; keepalive + retry prevents SSL EOF
# from crashing tasks when they dispatch the next step via .delay().
_redis_transport_opts = {
    'socket_keepalive': True,
    'retry_on_timeout': True,
    'socket_connect_timeout': 10,
    'socket_timeout': 30,
    'health_check_interval': 25,
}
CELERY_BROKER_TRANSPORT_OPTIONS = _redis_transport_opts
CELERY_REDIS_BACKEND_TRANSPORT_OPTIONS = _redis_transport_opts
# We track pipeline state in the DB; skip storing Celery results to avoid
# a second Redis round-trip that can hit the SSL EOF on result backend.
CELERY_TASK_IGNORE_RESULT = True

# Anthropic: prefer `backend/.env` if process env var is unset or looks truncated
_env_anthropic = _normalize_anthropic_key(os.getenv('ANTHROPIC_API_KEY', '') or '')
_file_anthropic = _normalize_anthropic_key(
    (dotenv_values(BASE_DIR / '.env') or {}).get('ANTHROPIC_API_KEY', '') or ''
)
if _env_anthropic and len(_env_anthropic) >= 40:
    ANTHROPIC_API_KEY = _env_anthropic
else:
    ANTHROPIC_API_KEY = _file_anthropic

# Claude model for agents + chat (Haiku = cheapest fast tier; override e.g. claude-sonnet-4-6 for quality)
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-haiku-4-5')
LLM_MAX_ATTEMPTS = int(os.getenv('LLM_MAX_ATTEMPTS', '4'))
LLM_RETRY_BASE_DELAY_SEC = float(os.getenv('LLM_RETRY_BASE_DELAY_SEC', '0.75'))

# Transcription: 'whisper_local' | 'mock'
TRANSCRIPTION_BACKEND = os.getenv('TRANSCRIPTION_BACKEND', 'mock')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')

# ChromaDB
CHROMA_DB_PATH = str(BASE_DIR / os.getenv('CHROMA_DB_PATH', 'chroma_db'))

# Chunk upload settings
CHUNK_UPLOAD_DIR = MEDIA_ROOT / 'chunks'
CHUNK_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

# Max file size: 4GB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB per request (chunks)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Global chat: max meetings to load for vector-search fallback only (see chat_agent)
CHAT_ALL_MEETINGS_FALLBACK_LIMIT = int(os.getenv('CHAT_ALL_MEETINGS_FALLBACK_LIMIT', '5'))

# Email — use SMTP if configured, otherwise console backend for dev
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'translateeIQ <noreply@translateeiq.com>')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
