import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_whisper_model = None
_whisper_model_name = None


def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """
    Transcribe audio file. Returns (raw_text, duration_string).
    Backend chosen via settings.TRANSCRIPTION_BACKEND:
      - 'whisper_local' : run openai-whisper locally (no API key required)
      - 'mock'          : return placeholder text (for development)
    """
    backend = getattr(settings, 'TRANSCRIPTION_BACKEND', 'mock')

    if backend == 'whisper_local':
        return _whisper_local(audio_path)
    return _mock_transcribe(audio_path)


def _whisper_local(audio_path: str) -> tuple[str, str]:
    """Transcribe using local Whisper model (openai-whisper package, no API key)."""
    global _whisper_model, _whisper_model_name
    try:
        import whisper
    except ImportError:
        raise ImportError('openai-whisper not installed. Run: pip install openai-whisper')

    model_name = getattr(settings, 'WHISPER_MODEL', 'base')
    if _whisper_model is None or _whisper_model_name != model_name:
        logger.info(f'Loading Whisper model: {model_name}')
        _whisper_model = whisper.load_model(model_name)
        _whisper_model_name = model_name
    model = _whisper_model

    logger.info(f'Transcribing: {audio_path}')
    result = model.transcribe(audio_path, verbose=False)

    raw_text = result['text'].strip()
    duration_secs = int(result.get('duration', 0))
    duration = _format_duration(duration_secs)

    return raw_text, duration


def _mock_transcribe(audio_path: str) -> tuple[str, str]:
    """Mock transcription for development — returns realistic placeholder."""
    logger.warning(f'Using MOCK transcription for {audio_path}')
    mock_text = (
        "Good morning everyone. Let's start today's meeting. "
        "Alice: I wanted to discuss the Q1 roadmap and our priorities. "
        "Bob: Sure, I think we should focus on the mobile improvements first. "
        "Carol: I agree. User research shows the onboarding flow has significant friction. "
        "Alice: That aligns with feedback from enterprise clients. Let's prioritize that. "
        "Bob: I can have a prototype ready by end of month. "
        "Carol: We should also review the pricing page based on conversion data. "
        "Alice: Good point. Let's schedule a separate session for pricing strategy. "
        "Bob: The API documentation also needs updating before the next release. "
        "Alice: Agreed. Let's wrap up — action items: Bob builds prototype, "
        "Carol compiles pricing data, I'll schedule the pricing meeting."
    )
    return mock_text, '45m'


def _format_duration(seconds: int) -> str:
    if seconds < 60:
        return f'{seconds}s'
    minutes = seconds // 60
    hours = minutes // 60
    if hours > 0:
        return f'{hours}h {minutes % 60}m'
    return f'{minutes}m'
