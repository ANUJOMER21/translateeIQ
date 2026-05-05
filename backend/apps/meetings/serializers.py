from rest_framework import serializers

from .media_storage import playback_url_path, uses_gcs_media
from .models import Meeting, UploadSession, Transcript, Summary, MOM


def pipeline_percent(meeting):
    """
    Matches upload_progress VIEW mapping so UI polls one consistent scale (0–100).
    uploading → 0–40 from chunk receipts; assembling/indexing/transcribing/analyzing use fixed checkpoints.
    """
    status_progress = {
        'assembling': 42,
        'transcribing': 50,
        'analyzing': 75,
        'indexing': 90,
        'completed': 100,
        'error': -1,
    }
    if meeting.status == 'uploading':
        try:
            s = meeting.upload_session
            if s.total_chunks and s.total_chunks > 0:
                up = int((s.received_chunks / s.total_chunks) * 100)
                return int(up * 0.4)
            return 0
        except UploadSession.DoesNotExist:
            return 0
    return int(status_progress.get(meeting.status, 0))


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = ['segments', 'raw_text', 'created_at']


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ['bullet_points', 'tldr', 'decisions', 'action_items', 'topics', 'created_at']


class MOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = MOM
        fields = ['decisions', 'action_items', 'notes', 'attendees', 'agenda', 'discussion', 'created_at']


class MeetingListSerializer(serializers.ModelSerializer):
    participants = serializers.ReadOnlyField()
    upload_session_id = serializers.SerializerMethodField()
    chunk_upload_percent = serializers.SerializerMethodField()
    pipeline_percent = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'original_filename', 'file_type',
            'duration', 'file_size', 'status', 'processing_step', 'participants',
            'upload_session_id', 'chunk_upload_percent', 'pipeline_percent',
            'created_at', 'updated_at',
        ]

    def get_upload_session_id(self, obj):
        try:
            return str(obj.upload_session.session_id)
        except UploadSession.DoesNotExist:
            return None

    def get_chunk_upload_percent(self, obj):
        if obj.status != 'uploading':
            return None
        try:
            return obj.upload_session.progress_pct
        except UploadSession.DoesNotExist:
            return None

    def get_pipeline_percent(self, obj):
        return pipeline_percent(obj)


class MeetingDetailSerializer(serializers.ModelSerializer):
    participants = serializers.ReadOnlyField()
    transcript = TranscriptSerializer(read_only=True)
    summary = SummarySerializer(read_only=True)
    mom = MOMSerializer(read_only=True)
    upload_session_id = serializers.SerializerMethodField()
    chunk_upload_percent = serializers.SerializerMethodField()
    pipeline_percent = serializers.SerializerMethodField()
    playback_url = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'original_filename', 'file_type',
            'duration', 'file_size', 'status', 'processing_step', 'error_message',
            'upload_session_id', 'chunk_upload_percent', 'pipeline_percent',
            'playback_url',
            'participants', 'transcript', 'summary', 'mom',
            'created_at', 'updated_at',
        ]

    def get_upload_session_id(self, obj):
        try:
            return str(obj.upload_session.session_id)
        except UploadSession.DoesNotExist:
            return None

    def get_chunk_upload_percent(self, obj):
        if obj.status != 'uploading':
            return None
        try:
            return obj.upload_session.progress_pct
        except UploadSession.DoesNotExist:
            return None

    def get_pipeline_percent(self, obj):
        return pipeline_percent(obj)

    def get_playback_url(self, obj):
        """Signed GCS URL or same-origin /media/... path for browser playback."""
        raw = (getattr(obj, 'file_path', None) or '').strip()
        if not raw:
            return None
        try:
            path_or_url = playback_url_path(raw)
        except Exception:
            return None
        if not path_or_url:
            return None
        if uses_gcs_media() or path_or_url.startswith('http'):
            return path_or_url
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(path_or_url)
        return path_or_url


class UploadInitSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=500)
    file_size = serializers.IntegerField(min_value=1)
    total_chunks = serializers.IntegerField(min_value=1)
    meeting_title = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ChunkUploadSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    chunk_index = serializers.IntegerField(min_value=0)
    chunk = serializers.FileField()


class UploadCompleteSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    scope = serializers.ChoiceField(choices=['this', 'all'], default='all')
    meeting_id = serializers.UUIDField(required=False, allow_null=True)
