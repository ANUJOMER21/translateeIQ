"""Normalize Redis URLs before Celery parses them (requires ssl_cert_reqs on rediss://)."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def ensure_rediss_ssl_cert_reqs(url: str) -> str:
    """Celery 5.3+ / redis backend requires ssl_cert_reqs query param on rediss:// URLs."""
    if not url or not url.startswith('rediss://'):
        return url
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if q.get('ssl_cert_reqs'):
        return url
    q['ssl_cert_reqs'] = 'CERT_REQUIRED'
    return urlunparse(parsed._replace(query=urlencode(q)))


def patch_celery_redis_env_from_os() -> None:
    """Fix raw Cloud Run / shell env vars before django.setup() or Celery binds the broker."""
    import os

    for key in ('CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND'):
        raw = os.environ.get(key)
        if not raw:
            continue
        fixed = ensure_rediss_ssl_cert_reqs(raw.strip())
        if fixed != raw:
            os.environ[key] = fixed
