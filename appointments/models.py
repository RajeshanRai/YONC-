from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from zoneinfo import ZoneInfo

from experts.models import ExpertProfile


class TimeSlot(models.Model):
    expert = models.ForeignKey(
        ExpertProfile,
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    discussion_topic = models.CharField(max_length=200, blank=True, help_text='What this time slot is best suited for')
    meeting_link = models.URLField(blank=True, help_text='Zoom, Teams, or other meeting URL')
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]
    days_of_week = models.CharField(max_length=50, blank=True, help_text='Weekdays available for this slot')
    expert_timezone = models.CharField(max_length=64, blank=True, default='', help_text='Timezone used by expert when creating this slot')
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        unique_together = [['expert', 'start_time']]

    def __str__(self):
        local_start = timezone.localtime(self.start_time)
        return f"{self.expert.user.get_full_name_display()} – {local_start.strftime('%b %d, %Y %I:%M %p')}"

    @property
    def days_of_week_list(self):
        if not self.days_of_week:
            return []
        return [day for day in self.days_of_week.split(',') if day]

    @property
    def days_of_week_display(self):
        selected = self.days_of_week_list
        if not selected:
            return 'Everyday'
        all_codes = [code for code, _ in self.DAYS_OF_WEEK]
        if set(selected) == set(all_codes):
            return 'Everyday'
        labels = [label for code, label in self.DAYS_OF_WEEK if code in selected]
        return ', '.join(labels)

    @property
    def booked_count(self):
        return self.appointment.exclude(status='cancelled').count()

    @property
    def remaining_capacity(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_available(self):
        return self.remaining_capacity > 0 and self.start_time >= timezone.now()

    def update_booked_status(self):
        self.is_booked = self.remaining_capacity == 0
        self.save(update_fields=['is_booked'])

    def get_display_window(self):
        local_start = timezone.localtime(self.start_time)
        local_end = timezone.localtime(self.end_time)
        return f"{local_start.strftime('%b %d, %Y %I:%M %p')} – {local_end.strftime('%I:%M %p')}"

    def get_expert_display_window(self):
        tz_name = self.expert_timezone or timezone.get_default_timezone_name()
        try:
            source_tz = ZoneInfo(tz_name)
        except Exception:
            source_tz = timezone.get_default_timezone()
            tz_name = timezone.get_default_timezone_name()

        start_at_source = timezone.localtime(self.start_time, source_tz)
        end_at_source = timezone.localtime(self.end_time, source_tz)
        return f"{start_at_source.strftime('%b %d, %Y %I:%M %p')} – {end_at_source.strftime('%I:%M %p')} ({tz_name})"


class Appointment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    expert = models.ForeignKey(
        ExpertProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    timeslot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        related_name='appointment'
    )
    subject = models.CharField(max_length=150)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        local_start = timezone.localtime(self.timeslot.start_time)
        return f"{self.subject} with {self.expert.user.get_full_name_display()} on {local_start.strftime('%b %d, %Y')}"

    def get_absolute_url(self):
        return reverse('appointments:appointment_detail', kwargs={'pk': self.pk})

    def get_appointment_window(self):
        return self.timeslot.get_display_window()
