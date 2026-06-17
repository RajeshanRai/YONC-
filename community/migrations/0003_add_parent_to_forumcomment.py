"""
Generated migration to add parent field for threaded comments.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_alter_forumpost_category_delete_forumcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumcomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='community.forumcomment'),
        ),
    ]
