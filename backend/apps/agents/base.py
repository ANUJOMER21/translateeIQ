import json
import re
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


def call_llm(
    system_prompt: str,
    user_content: str,
    json_mode: bool = True,
    *,
    max_tokens: int = 8192,
) -> dict | str:
    """
    Call Anthropic Claude (model from settings.ANTHROPIC_MODEL, default Haiku).
    Returns parsed dict if json_mode=True, else plain string.
    Falls back to mock data when ANTHROPIC_API_KEY is not set.

    max_tokens: default 8192; transcript formatting passes higher (see transcript_agent).
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    model = getattr(settings, 'ANTHROPIC_MODEL', 'claude-haiku-4-5')

    if not api_key or api_key.startswith('sk-ant-your'):
        logger.warning('No Anthropic API key — returning mock agent response')
        return _mock_response(system_prompt, json_mode)

    from anthropic import Anthropic
    from anthropic import APIStatusError

    client = Anthropic(api_key=api_key)

    system = system_prompt
    if json_mode:
        system += '\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no code fences.'

    message = None
    last_err = None
    max_attempts = getattr(settings, 'LLM_MAX_ATTEMPTS', 4)
    base_delay = getattr(settings, 'LLM_RETRY_BASE_DELAY_SEC', 0.75)
    for attempt in range(max_attempts):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{'role': 'user', 'content': user_content}],
            )
            break
        except APIStatusError as e:
            last_err = e
            retriable = getattr(e, 'status_code', None) in (429, 500, 503, 529)
            if not retriable or attempt >= max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning('Anthropic APIStatusError %s; retry in %.1fs', e.status_code, delay)
            time.sleep(delay)
        except Exception as e:
            last_err = e
            raise

    if message is None:
        raise last_err  # pragma: no cover

    content = message.content[0].text.strip()

    if json_mode:
        return _parse_json(content)
    return content


def _parse_json(text: str) -> dict:
    """Parse JSON, stripping markdown code fences if Claude wraps them."""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error(f'Failed to parse JSON from Claude response: {text[:200]}')
        return {}


def _mock_response(system_prompt: str, json_mode: bool):
    """Realistic mock data returned when ANTHROPIC_API_KEY is not configured."""
    prompt_lower = system_prompt.lower()

    if 'transcript' in prompt_lower:
        return {
            'segments': [
                {'id': 1, 'speaker': 'Alice', 'time': '0:00', 'text': "Good morning everyone. Let's start today's meeting."},
                {'id': 2, 'speaker': 'Bob',   'time': '0:30', 'text': 'I think we should focus on the mobile improvements first.'},
                {'id': 3, 'speaker': 'Carol', 'time': '1:15', 'text': 'User research shows the onboarding flow has significant friction.'},
                {'id': 4, 'speaker': 'Alice', 'time': '2:40', 'text': "Let's prioritize that for Q1."},
                {'id': 5, 'speaker': 'Bob',   'time': '3:10', 'text': 'I can have a prototype ready by end of month.'},
            ]
        }

    if 'summary' in prompt_lower:
        return {
            'bullet_points': [
                'Q1 roadmap reviewed — mobile onboarding improvements prioritized.',
                'User research confirmed friction in onboarding flow.',
                'Prototype delivery committed for end of month.',
                'Pricing page revision and API docs identified as next priorities.',
            ]
        }

    if 'mom' in prompt_lower or 'minutes' in prompt_lower:
        return {
            'decisions': [
                'Prioritize mobile onboarding improvements for Q1',
                'Schedule dedicated pricing strategy meeting',
                'Update API documentation before next release',
            ],
            'action_items': [
                {'owner': 'Bob',   'task': 'Deliver onboarding prototype',     'due': '2026-05-31'},
                {'owner': 'Carol', 'task': 'Compile pricing conversion data',  'due': '2026-05-15'},
                {'owner': 'Alice', 'task': 'Schedule pricing strategy meeting','due': '2026-05-10'},
            ],
            'notes': [
                'Enterprise clients flagged same onboarding friction',
                'Mobile traffic up 34% QoQ — high ROI improvement',
            ],
        }

    if json_mode:
        return {'response': 'Mock response — set ANTHROPIC_API_KEY for real Claude responses.'}
    return 'Mock response — set ANTHROPIC_API_KEY for real Claude responses.'
