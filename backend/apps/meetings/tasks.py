import logging
import os

from config.celery_app import app

logger = logging.getLogger(__name__)


def _set_step(meeting, step: str):
    meeting.processing_step = step
    meeting.save(update_fields=['processing_step'])


def _fail_meeting(meeting_id: str, exc: Exception):
    from apps.meetings.models import Meeting

    Meeting.objects.filter(pk=meeting_id).update(
        status='error',
        processing_step='',
        error_message=str(exc)[:2000],
    )


@app.task(bind=True, max_retries=3, default_retry_delay=15)
def assemble_meeting_task(self, session_id: str):
    from apps.meetings.media_storage import assemble_meeting_from_chunks, media_exists
    from apps.meetings.models import Meeting, UploadSession

    try:
        session = UploadSession.objects.select_related('meeting').get(pk=session_id)
    except UploadSession.DoesNotExist:
        logger.error('UploadSession %s not found', session_id)
        return

    meeting = session.meeting

    if meeting.status in ('transcribing', 'analyzing', 'indexing', 'completed'):
        logger.info('Meeting %s pipeline already started; skip assemble', meeting.id)
        if meeting.status == 'transcribing':
            transcribe_meeting_task.delay(str(meeting.id))
        return

    fp = (meeting.file_path or '').strip()
    if fp and media_exists(fp) and session.status == 'complete':
        logger.info('Meeting %s already assembled; continue pipeline', meeting.id)
        transcribe_meeting_task.delay(str(meeting.id))
        return

    try:
        _set_step(meeting, 'combining_chunks')
        rel = assemble_meeting_from_chunks(session, meeting)
        meeting.file_path = rel
        meeting.status = 'transcribing'
        meeting.processing_step = ''
        meeting.save(update_fields=['file_path', 'status', 'processing_step'])

        session.status = 'complete'
        session.save(update_fields=['status'])

        logger.info('Assembled meeting %s; starting transcribe', meeting.id)
        transcribe_meeting_task.delay(str(meeting.id))

    except Exception as e:
        logger.exception('Assembly failed for session %s: %s', session_id, e)
        meeting.status = 'error'
        meeting.processing_step = ''
        meeting.error_message = str(e)[:2000]
        meeting.save(update_fields=['status', 'processing_step', 'error_message'])
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, default_retry_delay=20)
def transcribe_meeting_task(self, meeting_id: str):
    from apps.meetings.media_storage import local_path_for_processing
    from apps.meetings.models import Meeting, Transcript
    from apps.pipeline.audio_extractor import extract_audio
    from apps.pipeline.transcriber import transcribe_audio

    try:
        meeting = Meeting.objects.get(pk=meeting_id)
    except Meeting.DoesNotExist:
        logger.error('Meeting %s not found', meeting_id)
        return

    if meeting.status in ('analyzing', 'indexing', 'completed'):
        logger.info('Meeting %s already past transcribe', meeting_id)
        return

    cleanup_paths: list[str] = []
    try:
        try:
            tr = meeting.transcript
            if (tr.raw_text or '').strip():
                logger.info('Meeting %s already transcribed; chaining analyze', meeting_id)
                analyze_meeting_task.delay(meeting_id)
                return
        except Exception:
            pass

        meeting.status = 'transcribing'
        meeting.processing_step = ''
        meeting.save(update_fields=['status', 'processing_step'])

        local_input, cleanup_paths = local_path_for_processing(meeting.file_path, meeting_id)
        audio_path = local_input

        if meeting.file_type == 'video':
            _set_step(meeting, 'extracting_audio')
            audio_path = extract_audio(local_input, meeting_id)
            cleanup_paths.append(audio_path)
            meeting.audio_path = audio_path
            meeting.save(update_fields=['audio_path'])

        _set_step(meeting, 'running_asr')
        raw_text, duration = transcribe_audio(audio_path)
        meeting.duration = duration
        meeting.save(update_fields=['duration'])

        Transcript.objects.update_or_create(
            meeting=meeting,
            defaults={'raw_text': raw_text, 'segments': []},
        )

        logger.info('Transcribed meeting %s; starting analyze', meeting_id)
        analyze_meeting_task.delay(meeting_id)

    except Exception as e:
        logger.exception('Transcribe failed for %s: %s', meeting_id, e)
        _fail_meeting(meeting_id, e)
        raise self.retry(exc=e)
    finally:
        for p in cleanup_paths:
            try:
                if p and os.path.isfile(p):
                    os.unlink(p)
            except OSError:
                pass


@app.task(bind=True, max_retries=3, default_retry_delay=20)
def analyze_meeting_task(self, meeting_id: str):
    from apps.agents.mom_agent import generate_mom
    from apps.agents.summary_agent import generate_summary
    from apps.agents.topics_agent import extract_topics
    from apps.agents.transcript_agent import format_transcript
    from apps.meetings.models import ActionItem, Meeting, MOM, MeetingTopic, Summary, Transcript

    try:
        meeting = Meeting.objects.select_related('transcript').get(pk=meeting_id)
        transcript = meeting.transcript
    except (Meeting.DoesNotExist, Transcript.DoesNotExist):
        logger.error('Meeting or transcript missing for %s', meeting_id)
        return

    if meeting.status in ('indexing', 'completed'):
        logger.info('Meeting %s already past analyze', meeting_id)
        return

    if (
        transcript.segments
        and Summary.objects.filter(meeting=meeting).exists()
        and MOM.objects.filter(meeting=meeting).exists()
    ):
        logger.info('Meeting %s already analyzed; chaining index', meeting_id)
        index_meeting_task.delay(meeting_id)
        return

    raw_text = (transcript.raw_text or '').strip()
    if not raw_text:
        _fail_meeting(meeting_id, ValueError('Empty transcript'))
        return

    try:
        meeting.status = 'analyzing'
        meeting.processing_step = ''
        meeting.save(update_fields=['status', 'processing_step'])

        _set_step(meeting, 'formatting_transcript')
        segments = format_transcript(raw_text, meeting.title)
        transcript.segments = segments
        transcript.save(update_fields=['segments'])

        _set_step(meeting, 'generating_summary')
        summary_data = generate_summary(raw_text)
        Summary.objects.update_or_create(
            meeting=meeting,
            defaults={
                'bullet_points': summary_data.get('bullet_points', []),
                'tldr': summary_data.get('tldr', ''),
                'decisions': summary_data.get('decisions', []),
                'action_items': summary_data.get('action_items', []),
                'topics': summary_data.get('topics', []),
            },
        )

        _set_step(meeting, 'generating_mom')
        mom_data = generate_mom(raw_text)
        MOM.objects.update_or_create(
            meeting=meeting,
            defaults={
                'decisions': mom_data.get('decisions', []),
                'action_items': mom_data.get('action_items', []),
                'notes': mom_data.get('notes', []),
                'attendees': mom_data.get('attendees', []),
                'agenda': mom_data.get('agenda', []),
                'discussion': mom_data.get('discussion', ''),
            },
        )

        # Persist ActionItem rows from MOM (idempotent: delete+recreate)
        ActionItem.objects.filter(meeting=meeting).delete()
        ai_rows = [
            ActionItem(
                meeting=meeting,
                task=item.get('task', ''),
                owner=item.get('owner', ''),
                due_date=item.get('due', ''),
            )
            for item in mom_data.get('action_items', [])
            if item.get('task', '').strip()
        ]
        if ai_rows:
            ActionItem.objects.bulk_create(ai_rows)

        # Extract and persist topics
        _set_step(meeting, 'extracting_topics')
        topics = extract_topics(raw_text)
        MeetingTopic.objects.filter(meeting=meeting).delete()
        if topics:
            MeetingTopic.objects.bulk_create([
                MeetingTopic(meeting=meeting, topic=t) for t in topics
            ])

        logger.info('Analyzed meeting %s; starting index', meeting_id)
        index_meeting_task.delay(meeting_id)

    except Exception as e:
        logger.exception('Analyze failed for %s: %s', meeting_id, e)
        _fail_meeting(meeting_id, e)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=2, default_retry_delay=10)
def index_meeting_task(self, meeting_id: str):
    from apps.meetings.models import Meeting, Transcript
    from apps.vector_store.store import index_meeting as chroma_index

    try:
        meeting = Meeting.objects.get(pk=meeting_id)
        transcript = meeting.transcript
    except (Meeting.DoesNotExist, Transcript.DoesNotExist):
        logger.error('Meeting or transcript missing for index %s', meeting_id)
        return

    if meeting.status == 'completed':
        return

    try:
        meeting.status = 'indexing'
        meeting.processing_step = ''
        meeting.save(update_fields=['status', 'processing_step'])

        _set_step(meeting, 'building_vectors')
        segments = transcript.segments or []
        chroma_index(
            str(meeting.id),
            segments,
            transcript.raw_text or '',
            meeting.title,
            owner_id=meeting.owner_id,
        )

        meeting.status = 'completed'
        meeting.processing_step = ''
        meeting.error_message = ''
        meeting.save(update_fields=['status', 'processing_step', 'error_message'])
        logger.info('Meeting %s processing complete', meeting_id)
        send_completion_email_task.delay(str(meeting.id))

    except Exception as e:
        logger.exception('Index failed for %s: %s', meeting_id, e)
        _fail_meeting(meeting_id, e)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_meeting_task(self, meeting_id: str):
    """Legacy entrypoint: use when meeting already has file_path set."""
    transcribe_meeting_task.delay(meeting_id)


@app.task
def send_completion_email_task(meeting_id: str):
    """Send email digest when a meeting finishes processing. Includes a public share link."""
    from django.conf import settings as dj_settings
    from django.core.mail import EmailMultiAlternatives
    from apps.meetings.models import Meeting, MeetingShareToken

    try:
        meeting = Meeting.objects.select_related('owner').get(pk=meeting_id)
    except Meeting.DoesNotExist:
        return

    user = meeting.owner
    if not user or not user.email:
        return

    try:
        if not user.preferences.email_notifications:
            return
    except Exception:
        pass

    # Get or create a permanent public share token
    share, _ = MeetingShareToken.objects.get_or_create(meeting=meeting)

    frontend_url = dj_settings.FRONTEND_URL.rstrip('/')
    public_url = f'{frontend_url}/share/{share.token}'
    app_url = f'{frontend_url}/meetings/{meeting.id}'

    name = user.first_name or user.email.split('@')[0]
    subject = f'Your transcript is ready: {meeting.title}'

    text_body = (
        f'Hi {name},\n\n'
        f'Your meeting "{meeting.title}" has been transcribed and is ready to view.\n\n'
        f'View the full transcript, summary, and action items (no login needed):\n'
        f'{public_url}\n\n'
        f'Or open it in the app:\n{app_url}\n\n'
        f'— translateeIQ\n\n'
        f'To stop these emails, visit your profile settings.'
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#1a1612;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#1a1612;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#211d18;border-radius:12px;overflow:hidden;border:1px solid #3a332a;">
        <!-- Header -->
        <tr>
          <td style="padding:28px 36px 20px;border-bottom:1px solid #3a332a;">
            <span style="font-size:18px;font-weight:700;color:#e8d5a3;letter-spacing:-0.3px;">translatee<b style="color:#c9972c;">IQ</b></span>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:32px 36px;">
            <p style="margin:0 0 6px;font-size:13px;color:#8a7a65;text-transform:uppercase;letter-spacing:0.06em;">Transcription complete</p>
            <h1 style="margin:0 0 20px;font-size:22px;font-weight:700;color:#f0e6d0;line-height:1.3;">{meeting.title}</h1>
            <p style="margin:0 0 28px;font-size:14px;color:#b09a7e;line-height:1.6;">
              Hi {name}, your recording has been fully processed. The transcript, AI summary, and minutes of meeting are ready.
            </p>
            <!-- CTA -->
            <table cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              <tr>
                <td style="background:#c9972c;border-radius:8px;">
                  <a href="{public_url}" style="display:inline-block;padding:14px 28px;font-size:14px;font-weight:600;color:#1a1208;text-decoration:none;border-radius:8px;">
                    View Meeting Details →
                  </a>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 4px;font-size:12px;color:#6a5c48;">No login required — this link is shareable with anyone.</p>
            <p style="margin:0;font-size:12px;color:#6a5c48;">Or <a href="{app_url}" style="color:#c9972c;text-decoration:none;">open in the app</a> for the full experience.</p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:20px 36px;border-top:1px solid #3a332a;">
            <p style="margin:0;font-size:11px;color:#5a4e40;">You're receiving this because email notifications are enabled for your account. <a href="{app_url.rsplit('/meetings', 1)[0]}/profile" style="color:#8a7a65;text-decoration:none;">Unsubscribe</a></p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    try:
        msg = EmailMultiAlternatives(subject, text_body, dj_settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=True)
        logger.info('Sent completion email for meeting %s to %s', meeting_id, user.email)
    except Exception as e:
        logger.warning('Failed to send email for meeting %s: %s', meeting_id, e)
