import io
import logging
from pathlib import Path

from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.db.models import Count
from django.utils import timezone

from .media_storage import save_upload_chunk
from .models import ActionItem, Meeting, MeetingShareToken, MeetingTopic, UploadChunk, UploadSession, Transcript, Summary, MOM
from .serializers import (
    MeetingListSerializer, MeetingDetailSerializer,
    UploadInitSerializer, ChunkUploadSerializer,
    UploadCompleteSerializer, ChatRequestSerializer,
    TranscriptSerializer, SummarySerializer, MOMSerializer,
    pipeline_percent as meeting_pipeline_percent,
)

logger = logging.getLogger(__name__)

ALLOWED_VIDEO_EXT = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
ALLOWED_AUDIO_EXT = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}


class MeetingPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


def _meeting_for_user(user, meeting_id):
    try:
        return Meeting.objects.select_related('upload_session').get(pk=meeting_id, owner=user)
    except Meeting.DoesNotExist:
        raise Http404


def get_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_VIDEO_EXT:
        return 'video'
    if ext in ALLOWED_AUDIO_EXT:
        return 'audio'
    return 'unknown'


# ─── Meeting endpoints ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_list(request):
    paginator = MeetingPagination()
    meetings = Meeting.objects.select_related('upload_session').filter(owner=request.user).order_by('-created_at')
    page = paginator.paginate_queryset(meetings, request)
    serializer = MeetingListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def meeting_detail(request, meeting_id):
    meeting = _meeting_for_user(request.user, meeting_id)

    if request.method == 'GET':
        serializer = MeetingDetailSerializer(meeting, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PATCH':
        if 'title' in request.data:
            meeting.title = request.data['title']
            meeting.save(update_fields=['title'])
            meeting.refresh_from_db()
        serializer = MeetingDetailSerializer(meeting, context={'request': request})
        return Response(serializer.data)

    if request.method == 'DELETE':
        meeting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_transcript(request, meeting_id):
    try:
        meeting = Meeting.objects.get(pk=meeting_id, owner=request.user)
        transcript = meeting.transcript
    except (Meeting.DoesNotExist, Transcript.DoesNotExist):
        raise Http404
    return Response(TranscriptSerializer(transcript).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_summary(request, meeting_id):
    try:
        meeting = Meeting.objects.get(pk=meeting_id, owner=request.user)
        summary = meeting.summary
    except (Meeting.DoesNotExist, Summary.DoesNotExist):
        raise Http404
    return Response(SummarySerializer(summary).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_mom(request, meeting_id):
    try:
        meeting = Meeting.objects.get(pk=meeting_id, owner=request.user)
        mom = meeting.mom
    except (Meeting.DoesNotExist, MOM.DoesNotExist):
        raise Http404
    return Response(MOMSerializer(mom).data)


# ─── Upload endpoints ─────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_init(request):
    """Initialize a chunked upload session."""
    ser = UploadInitSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    filename = d['filename']
    file_type = get_file_type(filename)
    if file_type == 'unknown':
        return Response(
            {'error': 'Unsupported file type. Use MP4, MOV, AVI, MKV, MP3, WAV, M4A, FLAC.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    title = d.get('meeting_title') or Path(filename).stem

    meeting = Meeting.objects.create(
        owner=request.user,
        title=title,
        original_filename=filename,
        file_type=file_type,
        file_size=d['file_size'],
        status='uploading',
    )

    session = UploadSession.objects.create(
        meeting=meeting,
        total_chunks=d['total_chunks'],
        total_size=d['file_size'],
    )

    return Response({
        'session_id': str(session.session_id),
        'meeting_id': str(meeting.id),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_chunk(request):
    """Receive a single chunk."""
    ser = ChunkUploadSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        session = UploadSession.objects.select_related('meeting').get(
            pk=d['session_id'],
            meeting__owner=request.user,
        )
    except UploadSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

    if session.status not in ('uploading',):
        return Response({'error': f'Session status is {session.status}'}, status=status.HTTP_400_BAD_REQUEST)

    chunk_index = d['chunk_index']
    save_upload_chunk(session.session_id, chunk_index, d['chunk'])

    with transaction.atomic():
        locked = UploadSession.objects.select_for_update().get(pk=session.pk)
        _chunk, created = UploadChunk.objects.get_or_create(
            session=locked,
            chunk_index=chunk_index,
        )
        if created:
            UploadSession.objects.filter(pk=locked.pk).update(
                received_chunks=F('received_chunks') + 1
            )

    session.refresh_from_db(fields=['received_chunks', 'total_chunks'])
    stored = UploadChunk.objects.filter(session=session).count()

    return Response({
        'received_chunks': stored,
        'total_chunks': session.total_chunks,
        'progress_pct': session.progress_pct,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_complete(request):
    """Validate chunks, mark assembling, enqueue worker assembly + pipeline (non-blocking)."""
    from .tasks import assemble_meeting_task

    ser = UploadCompleteSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    try:
        session = UploadSession.objects.select_related('meeting').get(
            pk=ser.validated_data['session_id'],
            meeting__owner=request.user,
        )
    except UploadSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

    meeting = session.meeting
    stored = UploadChunk.objects.filter(session=session).count()

    if stored < session.total_chunks:
        return Response({
            'error': f'Only {stored}/{session.total_chunks} chunks received'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            session = UploadSession.objects.select_for_update().select_related('meeting').get(
                pk=ser.validated_data['session_id'],
                meeting__owner=request.user,
            )
            meeting = session.meeting
            if session.status not in ('uploading',) or meeting.status != 'uploading':
                pass
            else:
                session.status = 'assembling'
                meeting.status = 'assembling'
                session.save(update_fields=['status'])
                meeting.save(update_fields=['status'])
                sid = str(session.session_id)
                transaction.on_commit(lambda s=sid: assemble_meeting_task.delay(s))

        meeting.refresh_from_db(fields=['status'])
        return Response({
            'meeting_id': str(meeting.id),
            'status': meeting.status,
        })

    except Exception as e:
        logger.exception('upload_complete failed for session %s', ser.validated_data['session_id'])
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upload_progress(request, session_id):
    """Poll upload + processing progress."""
    try:
        session = UploadSession.objects.select_related('meeting').get(
            pk=session_id,
            meeting__owner=request.user,
        )
    except UploadSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

    meeting = session.meeting

    overall_pct = float(meeting_pipeline_percent(meeting))

    return Response({
        'meeting_id': str(meeting.id),
        'upload_progress': session.progress_pct,
        'overall_progress': overall_pct,
        'stage': meeting.status,
        'step': meeting.processing_step or '',
        'error': meeting.error_message if meeting.status == 'error' else None,
    })


# ─── Chat endpoint ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """Chat with meeting AI agent."""
    from apps.agents.chat_agent import chat_with_meeting, chat_with_all_meetings

    ser = ChatRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    message = d['message']
    scope = d['scope']
    meeting_id = d.get('meeting_id')

    try:
        if scope == 'this' and meeting_id:
            try:
                meeting = Meeting.objects.prefetch_related(
                    'transcript', 'summary', 'mom'
                ).get(pk=meeting_id, owner=request.user)
            except Meeting.DoesNotExist:
                return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)
            response = chat_with_meeting(message, meeting)
        else:
            response = chat_with_all_meetings(message, request.user)

        return Response({'response': response})

    except Exception as e:
        logger.exception('Chat error')
        return Response(
            {'response': f'I encountered an error: {str(e)}. Please check your LLM API key (Anthropic).'},
            status=status.HTTP_200_OK,
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'ok'})


# ─── Dashboard ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Aggregated dashboard data: stats, recent meetings, action item counts, active uploads."""
    user = request.user
    meetings_qs = Meeting.objects.filter(owner=user)

    total = meetings_qs.count()
    completed = meetings_qs.filter(status='completed').count()
    processing = meetings_qs.filter(status__in=['assembling', 'transcribing', 'analyzing', 'indexing']).count()
    active_uploads = meetings_qs.filter(status__in=['uploading', 'assembling']).count()

    # New completed meetings in last 7 days
    week_ago = timezone.now() - timezone.timedelta(days=7)
    new_transcripts = meetings_qs.filter(status='completed', updated_at__gte=week_ago).count()

    # Action items open count
    open_action_items = ActionItem.objects.filter(meeting__owner=user, is_done=False).count()

    # Hours saved: rough estimate 10 min per meeting-hour of processing
    # Use duration if available — sum all completed meeting durations
    hours_saved = round(completed * 0.5, 1)  # 30 min avg per meeting as fallback

    recent = meetings_qs.select_related('upload_session').order_by('-created_at')[:5]
    from .serializers import MeetingListSerializer
    recent_data = MeetingListSerializer(recent, many=True).data

    return Response({
        'greeting': request.user.username or request.user.email.split('@')[0],
        'stats': {
            'total': total,
            'completed': completed,
            'processing': processing,
            'hours_saved': hours_saved,
            'active_uploads': active_uploads,
            'new_transcripts': new_transcripts,
            'open_action_items': open_action_items,
        },
        'recent_meetings': recent_data,
    })


# ─── Action Items ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def action_items_list(request):
    """All action items across user's meetings."""
    items = (
        ActionItem.objects
        .filter(meeting__owner=request.user)
        .select_related('meeting')
        .order_by('is_done', 'created_at')
    )
    data = [
        {
            'id': item.id,
            'task': item.task,
            'owner': item.owner,
            'due_date': item.due_date,
            'is_done': item.is_done,
            'meeting_id': str(item.meeting_id),
            'meeting_title': item.meeting.title,
            'created_at': item.created_at.isoformat(),
        }
        for item in items
    ]
    return Response(data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def action_item_toggle(request, item_id):
    """Toggle is_done for an action item."""
    try:
        item = ActionItem.objects.get(pk=item_id, meeting__owner=request.user)
    except ActionItem.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    item.is_done = not item.is_done
    item.save(update_fields=['is_done'])
    return Response({'id': item.id, 'is_done': item.is_done})


# ─── Trending Topics ──────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending_topics(request):
    """Top topics from user's meetings in the last 30 days, ranked by mention count."""
    since = timezone.now() - timezone.timedelta(days=30)
    topics = (
        MeetingTopic.objects
        .filter(meeting__owner=request.user, meeting__created_at__gte=since)
        .values('topic')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    return Response([{'topic': t['topic'], 'count': t['count']} for t in topics])


# ─── PDF Download ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_pdf(request, meeting_id):
    """Download a professional MOM PDF for the given meeting."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )

    try:
        meeting = Meeting.objects.get(pk=meeting_id, owner=request.user)
    except Meeting.DoesNotExist:
        raise Http404

    try:
        mom = meeting.mom
    except MOM.DoesNotExist:
        raise Http404

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'MOMTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=4,
        textColor=colors.HexColor('#1a1a2e'),
        fontName='Helvetica-Bold',
    )
    style_subtitle = ParagraphStyle(
        'MOMSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        textColor=colors.HexColor('#555555'),
    )
    style_section_heading = ParagraphStyle(
        'MOMSectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=4,
        textColor=colors.HexColor('#1a1a2e'),
        fontName='Helvetica-Bold',
    )
    style_body = ParagraphStyle(
        'MOMBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leading=15,
        textColor=colors.HexColor('#333333'),
    )
    style_bullet = ParagraphStyle(
        'MOMBullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3,
        leading=14,
        leftIndent=14,
        bulletIndent=0,
        textColor=colors.HexColor('#333333'),
    )
    style_footer = ParagraphStyle(
        'MOMFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#aaaaaa'),
        alignment=1,
    )

    story = []

    # Header: title
    story.append(Paragraph(meeting.title, style_title))

    # Sub-header: date · duration
    date_str = meeting.created_at.strftime('%B %d, %Y') if meeting.created_at else ''
    duration_str = meeting.duration or ''
    if date_str and duration_str:
        subheader = f"{date_str} &nbsp;&bull;&nbsp; Duration: {duration_str}"
    elif date_str:
        subheader = date_str
    else:
        subheader = ''
    if subheader:
        story.append(Paragraph(subheader, style_subtitle))

    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=8))

    # Attendees
    story.append(Paragraph('Attendees', style_section_heading))
    attendees = mom.attendees or []
    if attendees:
        for attendee in attendees:
            story.append(Paragraph(f'• {attendee}', style_bullet))
    else:
        story.append(Paragraph(f'• {meeting.title}', style_bullet))

    # Agenda
    story.append(Paragraph('Agenda', style_section_heading))
    agenda = mom.agenda or []
    if agenda:
        for i, item in enumerate(agenda, 1):
            story.append(Paragraph(f'{i}. {item}', style_bullet))
    else:
        story.append(Paragraph('No agenda items recorded.', style_body))

    # Discussion
    story.append(Paragraph('Discussion', style_section_heading))
    discussion = (mom.discussion or '').strip()
    if discussion:
        for para in discussion.split('\n\n'):
            para = para.strip()
            if para:
                story.append(Paragraph(para, style_body))
                story.append(Spacer(1, 4))
    else:
        story.append(Paragraph('No discussion notes recorded.', style_body))

    # Decisions
    story.append(Paragraph('Decisions', style_section_heading))
    decisions = mom.decisions or []
    if decisions:
        for i, decision in enumerate(decisions, 1):
            story.append(Paragraph(f'{i}. {decision}', style_bullet))
    else:
        story.append(Paragraph('No decisions recorded.', style_body))

    # Action Items table
    story.append(Paragraph('Action Items', style_section_heading))
    action_items = mom.action_items or []
    if action_items:
        table_data = [['Owner', 'Task', 'Due']]
        for item in action_items:
            table_data.append([
                item.get('owner', ''),
                item.get('task', ''),
                item.get('due', 'TBD'),
            ])

        col_widths = [3.5 * cm, 10 * cm, 3 * cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ]))
        story.append(table)
    else:
        story.append(Paragraph('No action items recorded.', style_body))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=6))
    story.append(Paragraph('Generated by translateeIQ', style_footer))

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    safe_title = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in meeting.title)
    safe_title = safe_title.strip().replace(' ', '_')
    filename = f"mom_{safe_title}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─── Public share endpoint ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def public_meeting(request, token):
    """No-auth public view. Returns meeting + transcript + summary + MOM."""
    try:
        share = MeetingShareToken.objects.select_related('meeting').get(pk=token)
    except MeetingShareToken.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    meeting = share.meeting
    if meeting.status != 'completed':
        return Response({'detail': 'Meeting not yet available.'}, status=status.HTTP_404_NOT_FOUND)

    # Generate playback URL (signed GCS or local path)
    playback_url = None
    try:
        from .media_storage import playback_url_path, uses_gcs_media
        raw_path = (getattr(meeting, 'file_path', None) or '').strip()
        if raw_path:
            p = playback_url_path(raw_path)
            if p:
                if uses_gcs_media() or p.startswith('http'):
                    playback_url = p
                else:
                    playback_url = request.build_absolute_uri(p)
    except Exception:
        pass

    data = {
        'id': str(meeting.id),
        'title': meeting.title,
        'file_type': meeting.file_type,
        'duration': meeting.duration,
        'created_at': meeting.created_at.isoformat(),
        'original_filename': meeting.original_filename,
        'playback_url': playback_url,
    }

    try:
        tr = meeting.transcript
        data['transcript'] = TranscriptSerializer(tr).data
    except Transcript.DoesNotExist:
        data['transcript'] = None

    try:
        data['summary'] = SummarySerializer(meeting.summary).data
    except Summary.DoesNotExist:
        data['summary'] = None

    try:
        data['mom'] = MOMSerializer(meeting.mom).data
    except MOM.DoesNotExist:
        data['mom'] = None

    return Response(data)
