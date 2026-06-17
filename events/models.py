from django.db import models
from django.urls import reverse
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=False)
    is_ticketed = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_seats = models.PositiveIntegerField(default=0)
    registration_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'pk': self.pk})

    @property
    def registered_count(self):
        return self.registrations.count()

    @property
    def seats_remaining(self):
        if not self.total_seats:
            return None
        return max(self.total_seats - self.registered_count, 0)

    @property
    def is_full(self):
        return self.total_seats > 0 and self.registered_count >= self.total_seats

    @property
    def can_register(self):
        return self.is_ticketed and not self.is_full and self.start_time >= timezone.now()

    def display_time(self):
        if self.end_time:
            return f"{self.start_time.strftime('%b %d, %Y %I:%M %p')} – {self.end_time.strftime('%I:%M %p')}"
        return self.start_time.strftime('%b %d, %Y %I:%M %p')


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='event_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"
