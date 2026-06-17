"""Add likes M2M to ForumPost

Generated manually.
"""
from django.db import migrations, models
import django.conf


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_add_parent_to_forumcomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumpost',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_forum_posts', to=django.conf.settings.AUTH_USER_MODEL),
        ),
    ]