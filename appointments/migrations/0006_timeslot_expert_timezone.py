from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0005_timeslot_days_of_week'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeslot',
            name='expert_timezone',
            field=models.CharField(blank=True, default='', help_text='Timezone used by expert when creating this slot', max_length=64),
        ),
    ]
