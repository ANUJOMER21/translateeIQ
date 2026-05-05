from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0005_actionitem_meetingtopic'),
    ]

    operations = [
        migrations.AddField(
            model_name='summary',
            name='tldr',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='summary',
            name='decisions',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='summary',
            name='action_items',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='summary',
            name='topics',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='mom',
            name='attendees',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='mom',
            name='agenda',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='mom',
            name='discussion',
            field=models.TextField(blank=True),
        ),
    ]
