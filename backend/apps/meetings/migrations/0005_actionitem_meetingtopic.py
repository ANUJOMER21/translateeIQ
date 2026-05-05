from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0004_meeting_processing_step'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task', models.TextField()),
                ('owner', models.CharField(blank=True, max_length=200)),
                ('due_date', models.CharField(blank=True, max_length=100)),
                ('is_done', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_items', to='meetings.meeting')),
            ],
            options={
                'ordering': ['created_at'],
                'app_label': 'meetings',
            },
        ),
        migrations.CreateModel(
            name='MeetingTopic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='meetings.meeting')),
            ],
            options={
                'ordering': ['topic'],
                'app_label': 'meetings',
            },
        ),
    ]
