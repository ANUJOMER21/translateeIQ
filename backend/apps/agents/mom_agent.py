import logging
from .base import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Minutes of Meeting (MOM) extraction agent.
Analyze the transcript and extract comprehensive structured meeting minutes.

Return a JSON object with this exact structure:
{
  "attendees": ["Name (role)", "Name — Department"],
  "agenda": ["Agenda item 1", "Agenda item 2"],
  "discussion": "2-4 paragraph narrative of what was discussed",
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {"owner": "Person Name", "task": "Task description", "due": "YYYY-MM-DD or 'TBD'"},
    ...
  ],
  "notes": ["Important contextual note 1", "Important contextual note 2"]
}

Rules:
- attendees: extract from speaker names appearing in the transcript; include role or department if inferable (e.g. "Alice (Engineering Lead)"); if role is unknown just use the name
- agenda: infer the agenda items from the topics and flow of the conversation (2-6 items)
- discussion: write as narrative prose in 2-4 paragraphs covering what was discussed, key context, and how the conversation unfolded
- decisions: 3-6 key decisions that were agreed upon during the meeting
- action_items: specific tasks with clear owners (use first name if known); use YYYY-MM-DD for dates or 'TBD' if not specified
- notes: important context, constraints, risks, or observations that don't fit elsewhere"""


def generate_mom(raw_text: str) -> dict:
    """Generate Minutes of Meeting from transcript. Returns full dict including attendees, agenda, discussion."""
    result = call_llm(SYSTEM_PROMPT, f"Transcript:\n{raw_text}", json_mode=True)
    return {
        'attendees': result.get('attendees', []),
        'agenda': result.get('agenda', []),
        'discussion': result.get('discussion', ''),
        'decisions': result.get('decisions', []),
        'action_items': result.get('action_items', []),
        'notes': result.get('notes', []),
    }
