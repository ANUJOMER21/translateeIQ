from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0003_uploadchunk'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='processing_step',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
