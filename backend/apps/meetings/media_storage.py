"""Chunk + meeting file I/O: local MEDIA_ROOT or shared GCS (split Cloud Run API + worker)."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def uses_gcs_media() -> bool:
    return bool(getattr(settings, 'GS_MEDIA_BUCKET', '') or '')


def chunk_relpath(session_id, chunk_index: int) -> str:
    return f'chunks/{session_id}/chunk_{chunk_index:06d}'


def meeting_file_relpath(meeting_id, original_filename: str) -> str:
    safe = Path(original_filename).name
    return f'meetings/{meeting_id}/{safe}'


def save_upload_chunk(session_id, chunk_index: int, uploaded_file) -> None:
    """Persist one chunk using default_storage (filesystem or GCS)."""
    name = chunk_relpath(session_id, chunk_index)
    uploaded_file.seek(0)
    default_storage.save(name, uploaded_file)


def _storage_exists(name: str) -> bool:
    """
    django-storages GCS 1.14.x has a bug where bucket.get_blob() returns None
    even when the object exists, causing exists() to always return False.
    Use open() as the authoritative check instead.
    """
    try:
        with default_storage.open(name, 'rb') as _f:
            _f.read(1)
        return True
    except (FileNotFoundError, OSError):
        return False


def media_exists(name: str) -> bool:
    if not name:
        return False
    p = Path(name)
    if p.is_absolute() and p.is_file():
        return True
    return _storage_exists(name)


def assemble_meeting_from_chunks(session, meeting) -> str:
    """
    Concatenate chunk_* into the final meeting file; delete chunks.
    Returns storage-relative path stored in Meeting.file_path.
    """
    final_name = meeting_file_relpath(meeting.id, meeting.original_filename)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=f'assemble_{meeting.id}_', suffix='.bin')
        os.close(fd)
        with open(tmp_path, 'wb') as out:
            for i in range(session.total_chunks):
                chunk_name = chunk_relpath(session.session_id, i)
                try:
                    with default_storage.open(chunk_name, 'rb') as ch:
                        shutil.copyfileobj(ch, out, length=1024 * 1024)
                except (FileNotFoundError, OSError):
                    raise FileNotFoundError(f'Missing chunk {i} for session {session.session_id}')
                default_storage.delete(chunk_name)

        with open(tmp_path, 'rb') as fh:
            default_storage.save(final_name, File(fh))
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return final_name


def local_path_for_processing(file_path_db: str, meeting_id: str) -> tuple[str, list[str]]:
    """
    Return a local filesystem path for ffmpeg / Whisper and a list of temp paths to delete.
    """
    to_cleanup: list[str] = []
    raw = (file_path_db or '').strip()
    if not raw:
        raise ValueError('Meeting has no file_path')

    p = Path(raw)
    if p.is_absolute() and p.is_file():
        return str(p), to_cleanup

    suffix = Path(raw).suffix or '.bin'
    fd, tmp_path = tempfile.mkstemp(prefix=f'm_{meeting_id}_src_', suffix=suffix)
    os.close(fd)
    to_cleanup.append(tmp_path)
    try:
        with default_storage.open(raw, 'rb') as src:
            with open(tmp_path, 'wb') as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
    except (FileNotFoundError, OSError):
        raise FileNotFoundError(f'Media not found: {raw}')
    return tmp_path, to_cleanup


def playback_url_path(file_path_db: str) -> str | None:
    """URL path or absolute URL for media playback (serializer)."""
    raw = (file_path_db or '').strip()
    if not raw:
        return None
    if uses_gcs_media():
        return default_storage.url(raw)
    p = Path(raw)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to(Path(settings.MEDIA_ROOT).resolve())
            rel_str = rel.as_posix()
        except ValueError:
            return None
    else:
        rel_str = raw.lstrip('/')
    base = settings.MEDIA_URL or '/media/'
    if not base.endswith('/'):
        base += '/'
    return f'{base}{rel_str}'
