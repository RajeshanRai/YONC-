from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
        ('community', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumpost',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forum_posts', to='services.servicecategory'),
        ),
        migrations.DeleteModel(
            name='ForumCategory',
        ),
    ]
