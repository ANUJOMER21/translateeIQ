import uuid

from django.conf import settings
from django.db import models


class Meeting(models.Model):
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('assembling', 'Assembling'),
        ('transcribing', 'Transcribing'),
        ('analyzing', 'Analyzing'),
        ('indexing', 'Indexing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]
    FILE_TYPE_CHOICES = [('video', 'Video'), ('audio', 'Audio')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meetings',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='video')
    file_path = models.CharField(max_length=1000, blank=True)
    audio_path = models.CharField(max_length=1000, blank=True)
    duration = models.CharField(max_length=50, blank=True)
    file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    processing_step = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'meetings'

    def __str__(self):
        return self.title

    @property
    def participants(self):
        """Extract unique speakers from transcript segments."""
        if hasattr(self, 'transcript') and self.transcript.segments:
            seen = []
            for seg in self.transcript.segments:
                sp = seg.get('speaker', '')
                if sp and sp not in seen:
                    seen.append(sp)
            return seen
        return []


class UploadSession(models.Model):
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('assembling', 'Assembling'),
        ('complete', 'Complete'),
        ('error', 'Error'),
    ]

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='upload_session')
    total_chunks = models.IntegerField(default=0)
    received_chunks = models.IntegerField(default=0)
    total_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'

    @property
    def progress_pct(self):
        if self.total_chunks == 0:
            return 0
        stored = self.chunks.count()
        return int((stored / self.total_chunks) * 100)


class UploadChunk(models.Model):
    """One row per received chunk — unique (session, index) for idempotent retries."""
    session = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    chunk_index = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'chunk_index'],
                name='meetings_uploadchunk_session_index_uniq',
            ),
        ]


class Transcript(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='transcript')
    raw_text = models.TextField(blank=True)
    # segments: [{id, speaker, time, text}]
    segments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'


class Summary(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='summary')
    # bullet_points: [str]
    bullet_points = models.JSONField(default=list)
    tldr = models.TextField(blank=True)
    decisions = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    topics = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'


class MOM(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='mom')
    # decisions: [str]
    decisions = models.JSONField(default=list)
    # action_items: [{owner, task, due}]
    action_items = models.JSONField(default=list)
    # notes: [str]
    notes = models.JSONField(default=list)
    attendees = models.JSONField(default=list)
    agenda = models.JSONField(default=list)
    discussion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'


class ActionItem(models.Model):
    """Persisted action items extracted from MOM — supports per-item done toggle."""
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='action_items')
    task = models.TextField()
    owner = models.CharField(max_length=200, blank=True)
    due_date = models.CharField(max_length=100, blank=True)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.task[:60]} ({self.meeting.title})'


class MeetingTopic(models.Model):
    """Topics extracted from a meeting — used for trending topics aggregation."""
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='topics')
    topic = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'
        ordering = ['topic']


class UserPreference(models.Model):
    """Per-user app preferences."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences',
    )
    email_notifications = models.BooleanField(default=True)

    class Meta:
        app_label = 'meetings'


class MeetingShareToken(models.Model):
    """Opaque token that grants public read-only access to a meeting."""
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='share_token')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'meetings'

    def __str__(self):
        return f'ShareToken({self.meeting.title})'
