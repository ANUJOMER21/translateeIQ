import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0002_meeting_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_index', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'session',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='chunks',
                        to='meetings.uploadsession',
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name='uploadchunk',
            constraint=models.UniqueConstraint(
                fields=('session', 'chunk_index'),
                name='meetings_uploadchunk_session_index_uniq',
            ),
        ),
    ]
