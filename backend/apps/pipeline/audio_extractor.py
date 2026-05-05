import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, meeting_id: str) -> str:
    """Extract audio from video file using ffmpeg. Returns path to a temp .wav (worker-safe, no shared MEDIA_ROOT)."""
    audio_path = os.path.join(tempfile.gettempdir(), f'meeting_{meeting_id}_audio.wav')

    try:
        result = subprocess.run(
            [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',                    # no video
                '-acodec', 'pcm_s16le',   # PCM 16-bit
                '-ar', '16000',           # 16kHz (Whisper optimal)
                '-ac', '1',               # mono
                audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if result.returncode != 0:
            raise RuntimeError(f'ffmpeg failed: {result.stderr}')
        logger.info(f'Audio extracted to {audio_path}')
        return audio_path

    except FileNotFoundError:
        # ffmpeg not installed — try moviepy fallback
        return _extract_with_moviepy(video_path, audio_path)


def _extract_with_moviepy(video_path: str, audio_path: str) -> str:
    """Fallback audio extraction using moviepy."""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec='pcm_s16le', logger=None)
        clip.close()
        return audio_path
    except Exception as e:
        raise RuntimeError(f'Audio extraction failed (no ffmpeg or moviepy): {e}')
