import logging
from .base import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a transcript formatting agent. Given raw meeting transcript text,
extract and format it into speaker-attributed segments with timestamps.

Return a JSON object with this exact structure:
{
  "segments": [
    {"id": 1, "speaker": "Speaker Name", "time": "0:00", "text": "What they said"},
    ...
  ]
}

Rules:
- Identify distinct speakers (use names if mentioned, else "Speaker 1", "Speaker 2", etc.)
- Estimate timestamps evenly based on text length if not present
- Keep each segment to 1-3 sentences
- Preserve the original wording closely
- Time format: M:SS or H:MM:SS"""


def format_transcript(raw_text: str, meeting_title: str = '') -> list:
    """Format raw transcript text into speaker segments."""
    user_content = f"Meeting: {meeting_title}\n\nTranscript:\n{raw_text}"
    # Large JSON (many segments × quoted text); Sonnet 4.x allows high max_tokens — cap cost vs truncation.
    result = call_llm(SYSTEM_PROMPT, user_content, json_mode=True, max_tokens=32768)
    segments = result.get('segments', [])
    # Ensure each segment has required fields
    cleaned = []
    for i, seg in enumerate(segments):
        cleaned.append({
            'id': i + 1,
            'speaker': seg.get('speaker', f'Speaker {i + 1}'),
            'time': seg.get('time', '0:00'),
            'text': seg.get('text', ''),
        })
    return cleaned
