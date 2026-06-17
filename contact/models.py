from django.db import models
from django.core.mail import send_mail
from django.conf import settings


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('partnership', 'Partnership'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    replied = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"

    def save(self, *args, **kwargs):
        # Send confirmation email to user
        if not self.pk:  # Only on creation
            try:
                send_mail(
                    subject='We received your message | Youth of Nepal in Canada',
                    message=f'Hi {self.name},\n\nThank you for reaching out to Youth of Nepal in Canada. We have received your message and will get back to you as soon as possible.\n\nBest regards,\nYouth of Nepal in Canada Team',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error sending email: {e}")

        super().save(*args, **kwargs)
