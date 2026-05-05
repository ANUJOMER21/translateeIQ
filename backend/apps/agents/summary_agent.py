import logging
from .base import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a meeting summarization agent. Given a meeting transcript,
create a comprehensive structured summary.

Return a JSON object with this exact structure:
{
  "tldr": "1-2 paragraph narrative summary of the meeting",
  "bullet_points": ["Key point 1 — specific and actionable", "Key point 2"],
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": [{"owner": "Name", "task": "Task description", "due": "Due date or TBD"}],
  "topics": ["Topic 1", "Topic 2"]
}

Rules:
- tldr: 2-3 sentences, narrative style capturing the overall purpose and outcome of the meeting
- bullet_points: 4-8 items, each a clear actionable sentence focused on decisions, outcomes, and key discussions
- decisions: 2-6 key decisions that were made or agreed upon during the meeting
- action_items: specific tasks assigned to individuals with clear owners and due dates (use 'TBD' if no date specified)
- topics: 3-8 short topic labels of 2-4 words each capturing the main subjects discussed
- Avoid filler and repetition across all fields"""


def generate_summary(raw_text: str) -> dict:
    """Generate structured summary from transcript. Returns full dict."""
    result = call_llm(SYSTEM_PROMPT, f"Transcript:\n{raw_text}", json_mode=True)
    return {
        'tldr': result.get('tldr', ''),
        'bullet_points': result.get('bullet_points', []),
        'decisions': result.get('decisions', []),
        'action_items': result.get('action_items', []),
        'topics': result.get('topics', []),
    }
