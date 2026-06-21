from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeslot',
            name='capacity',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
