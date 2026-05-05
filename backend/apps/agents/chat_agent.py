import logging

from django.conf import settings

from apps.meetings.models import Meeting
from apps.vector_store.store import query_meeting, query_all_meetings
from .base import call_llm

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """You are an intelligent meeting assistant with access to meeting transcripts, summaries, and action items.

Answer questions accurately and helpfully based on the provided context.
If the context doesn't contain the answer, say so clearly.
Keep responses concise but complete. Use bullet points for lists.
Do not make up information not present in the context."""


def _build_meeting_context(meeting) -> str:
    """Build a text context string from a meeting object."""
    parts = [f"Meeting: {meeting.title} ({meeting.created_at.strftime('%Y-%m-%d')})"]

    try:
        transcript = meeting.transcript
        if transcript.segments:
            parts.append("\nTranscript segments:")
            for seg in transcript.segments[:20]:  # limit context
                parts.append(f"  [{seg['time']}] {seg['speaker']}: {seg['text']}")
    except Exception:
        pass

    try:
        summary = meeting.summary
        if summary.bullet_points:
            parts.append("\nSummary:")
            for bp in summary.bullet_points:
                parts.append(f"  • {bp}")
    except Exception:
        pass

    try:
        mom = meeting.mom
        if mom.decisions:
            parts.append("\nDecisions:")
            for d in mom.decisions:
                parts.append(f"  • {d}")
        if mom.action_items:
            parts.append("\nAction Items:")
            for ai in mom.action_items:
                parts.append(f"  • {ai['task']} (Owner: {ai['owner']}, Due: {ai['due']})")
    except Exception:
        pass

    return '\n'.join(parts)


def chat_with_meeting(message: str, meeting) -> str:
    """Chat scoped to a single meeting."""
    # Try vector search first for relevant segments
    relevant_chunks = []
    try:
        relevant_chunks = query_meeting(str(meeting.id), message, n_results=5)
    except Exception:
        pass  # Fall back to full context

    if relevant_chunks:
        context = f"Meeting: {meeting.title}\n\nRelevant transcript segments:\n"
        context += '\n'.join(f"[{c['time']}] {c['speaker']}: {c['text']}" for c in relevant_chunks)
        # Append summary/MOM
        try:
            context += '\n\nSummary:\n' + '\n'.join(f'• {bp}' for bp in meeting.summary.bullet_points)
        except Exception:
            pass
        try:
            mom = meeting.mom
            context += '\n\nDecisions:\n' + '\n'.join(f'• {d}' for d in mom.decisions)
            context += '\n\nAction Items:\n' + '\n'.join(
                f'• {ai["task"]} ({ai["owner"]})' for ai in mom.action_items
            )
        except Exception:
            pass
    else:
        context = _build_meeting_context(meeting)

    user_content = f"Context:\n{context}\n\nQuestion: {message}"
    return call_llm(SYSTEM_TEMPLATE, user_content, json_mode=False)


def chat_with_all_meetings(message: str, user) -> str:
    """Chat across the signed-in user's meetings — vector search first; DB fallback is capped."""
    relevant_chunks = []
    try:
        relevant_chunks = query_all_meetings(message, n_results=8, owner_id=user.id)
    except Exception:
        pass

    if relevant_chunks:
        context = "Relevant segments from your meetings:\n\n"
        for chunk in relevant_chunks:
            context += f"[{chunk.get('meeting_title', 'Unknown')}] [{chunk.get('time', '')}] {chunk.get('speaker', '')}: {chunk.get('text', '')}\n"
    else:
        limit = getattr(settings, 'CHAT_ALL_MEETINGS_FALLBACK_LIMIT', 5)
        recent = (
            Meeting.objects.filter(status='completed', owner=user)
            .prefetch_related('transcript', 'summary', 'mom')
            .order_by('-updated_at')[:limit]
        )
        contexts = [_build_meeting_context(m) for m in recent]
        context = '\n\n---\n\n'.join(contexts) if contexts else 'No completed meetings found.'

    user_content = f"Context from all meetings:\n{context}\n\nQuestion: {message}"
    return call_llm(SYSTEM_TEMPLATE, user_content, json_mode=False)
