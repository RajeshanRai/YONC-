from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0004_add_likes_to_forumpost'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumcomment',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
    ]
