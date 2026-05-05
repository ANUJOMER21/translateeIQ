import logging
from .base import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a topic extraction agent. Given a meeting transcript, identify the key topics discussed.

Return a JSON object:
{
  "topics": ["Topic 1", "Topic 2", "Topic 3"]
}

Rules:
- 3-8 short topic labels (2-4 words each)
- Focus on substantive themes, not generic terms like "discussion" or "meeting"
- Examples: "Q3 budget review", "Mobile app stability", "Hiring plan", "API performance"
- Capitalize first word only"""


def extract_topics(raw_text: str) -> list:
    """Extract topic labels from transcript text."""
    try:
        result = call_llm(SYSTEM_PROMPT, f"Transcript:\n{raw_text[:4000]}", json_mode=True)
        return result.get('topics', [])
    except Exception as e:
        logger.warning('Topic extraction failed: %s', e)
        return []
