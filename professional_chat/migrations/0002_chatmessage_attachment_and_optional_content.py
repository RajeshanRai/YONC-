from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('professional_chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='chat_attachments/groups/'),
        ),
        migrations.AlterField(
            model_name='chatmessage',
            name='content',
            field=models.TextField(blank=True, default=''),
        ),
    ]