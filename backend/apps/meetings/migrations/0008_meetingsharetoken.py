import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0007_userpreference'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeetingShareToken',
            fields=[
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meeting', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='share_token',
                    to='meetings.meeting',
                )),
            ],
            options={'app_label': 'meetings'},
        ),
    ]
