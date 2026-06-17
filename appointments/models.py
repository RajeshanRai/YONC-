from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from experts.models import ExpertProfile


class TimeSlot(models.Model):
    expert = models.ForeignKey(
        ExpertProfile,
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        unique_together = [['expert', 'start_time']]

    def __str__(self):
        return f"{self.expert.user.get_full_name_display()} – {self.start_time.strftime('%b %d, %Y %I:%M %p')}"

    @property
    def is_available(self):
        return not self.is_booked and self.start_time >= timezone.now()

    def get_display_window(self):
        return f"{self.start_time.strftime('%b %d, %Y %I:%M %p')} – {self.end_time.strftime('%I:%M %p')}"


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
        return f"{self.subject} with {self.expert.user.get_full_name_display()} on {self.timeslot.start_time.strftime('%b %d, %Y')}"

    def get_absolute_url(self):
        return reverse('appointments:appointment_detail', kwargs={'pk': self.pk})

    def get_appointment_window(self):
        return self.timeslot.get_display_window()
