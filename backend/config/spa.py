"""Serve the Vite production bundle (index.html) for client-side routes."""
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404


def spa_index(request):
    index = Path(settings.STATIC_ROOT) / 'index.html'
    if not index.is_file():
        raise Http404(
            'Frontend bundle missing. For local dev use Vite (npm run dev). '
            'For production, build the SPA and run collectstatic.'
        )
    return FileResponse(index.open('rb'), content_type='text/html; charset=utf-8')
