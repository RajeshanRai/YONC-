from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_pendinguserregistration'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='chat_violation_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='is_blocked_for_chat_violations',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='chat_blocked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
