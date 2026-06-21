from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from services.models import ServiceCategory


class ExpertProfile(models.Model):
    """Profile for approved experts offering services."""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expert_profile')
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name='expert_profiles')
    
    # Professional details
    years_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(max_length=2000, help_text='Detailed professional biography')
    qualifications = models.TextField(max_length=1000, blank=True, help_text='Education, certifications')
    specialties = models.CharField(max_length=500, blank=True, help_text='Comma-separated specialties')
    
    # Contact info
    phone_number = models.CharField(max_length=20, blank=True)
    email_public = models.EmailField(blank=True, help_text='Public contact email (optional)')
    website = models.URLField(blank=True)
    
    # Location
    province = models.CharField(max_length=2, choices=settings.AUTH_USER_MODEL.PROVINCE_CHOICES if hasattr(settings.AUTH_USER_MODEL, 'PROVINCE_CHOICES') else [
        ('ON', 'Ontario'), ('BC', 'British Columbia'), ('AB', 'Alberta'), ('QC', 'Quebec'),
        ('MB', 'Manitoba'), ('SK', 'Saskatchewan'), ('NS', 'Nova Scotia'), ('NB', 'New Brunswick'),
        ('NL', 'Newfoundland and Labrador'), ('PE', 'Prince Edward Island'),
        ('NT', 'Northwest Territories'), ('YT', 'Yukon'), ('NU', 'Nunavut'),
    ])
    city = models.CharField(max_length=100)
    
    # Availability
    is_available = models.BooleanField(default=True)
    available_hours = models.CharField(max_length=200, blank=True, help_text='e.g., Mon-Fri 9AM-5PM')
    
    # Status
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_experts')
    
    # Social proof
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_consultations = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-rating', '-created_at']
        permissions = [
            ('can_approve_expert', 'Can approve expert applications'),
            ('can_feature_expert', 'Can feature experts'),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name_display()} - {self.category.name}"
    
    def get_absolute_url(self):
        return reverse('expert_detail', kwargs={'pk': self.pk})
    
    def get_initials(self):
        name = self.user.get_full_name() or self.user.username
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return name[:2].upper()
    
    def get_specialties_list(self):
        if self.specialties:
            return [s.strip() for s in self.specialties.split(',') if s.strip()]
        return []
    
    def get_total_years_experience(self):
        """Calculate total years of experience from ExpertExperience entries."""
        from datetime import date

        experiences = self.experiences.all()
        if not experiences:
            return self.years_experience

        intervals = []
        today = date.today()
        for exp in experiences:
            start_date = exp.start_date
            end_date = exp.end_date if exp.end_date else today
            if exp.is_current:
                end_date = today
            if end_date < start_date:
                continue
            intervals.append((start_date, end_date))

        if not intervals:
            return self.years_experience

        intervals.sort(key=lambda interval: interval[0])
        merged = [intervals[0]]
        for start_date, end_date in intervals[1:]:
            last_start, last_end = merged[-1]
            if start_date <= last_end:
                merged[-1] = (last_start, max(last_end, end_date))
            else:
                merged.append((start_date, end_date))

        total_days = sum((end_date - start_date).days for start_date, end_date in merged)
        total_years = int(total_days / 365.25)
        return total_years


class ExpertApplication(models.Model):
    """Applications from users who want to become experts."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expert_applications')
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT)
    
    years_experience = models.PositiveIntegerField()
    bio = models.TextField(max_length=2000)
    qualifications = models.TextField(max_length=1000, blank=True)
    specialties = models.CharField(max_length=500, blank=True)
    
    phone_number = models.CharField(max_length=20)
    province = models.CharField(max_length=2, choices=settings.AUTH_USER_MODEL.PROVINCE_CHOICES if hasattr(settings.AUTH_USER_MODEL, 'PROVINCE_CHOICES') else [
        ('ON', 'Ontario'), ('BC', 'British Columbia'), ('AB', 'Alberta'), ('QC', 'Quebec'),
        ('MB', 'Manitoba'), ('SK', 'Saskatchewan'), ('NS', 'Nova Scotia'), ('NB', 'New Brunswick'),
        ('NL', 'Newfoundland and Labrador'), ('PE', 'Prince Edward Island'),
        ('NT', 'Northwest Territories'), ('YT', 'Yukon'), ('NU', 'Nunavut'),
    ])
    city = models.CharField(max_length=100)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='reviewed_applications')
    review_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Application: {self.user.username} - {self.category.name} ({self.status})"
    
    def approve(self, reviewer=None):
        """Approve this application and create or update an ExpertProfile."""
        if self.status == 'approved':
            return

        self.status = 'approved'
        self.reviewed_at = timezone.now()
        if reviewer is not None:
            self.reviewed_by = reviewer
        self.save()

        profile_values = {
            'category': self.category,
            'years_experience': self.years_experience,
            'bio': self.bio,
            'qualifications': self.qualifications,
            'specialties': self.specialties,
            'phone_number': self.phone_number,
            'province': self.province,
            'city': self.city,
            'is_approved': True,
        }

        profile, created = ExpertProfile.objects.get_or_create(user=self.user, defaults=profile_values)
        if not created:
            for field, value in profile_values.items():
                setattr(profile, field, value)
            profile.save()

        self.user.role = 'expert'
        self.user.save()

        self.send_approval_email()

    def reject(self, reviewer=None):
        """Reject this application."""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        if reviewer is not None:
            self.reviewed_by = reviewer
        self.save()
        self.send_rejection_email()

    def send_rejection_email(self):
        """Send an email to the user when their application is rejected."""
        subject = 'Your expert application status on Youth of Nepal in Canada'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        recipient = self.user.email

        context = {
            'user': self.user,
            'category': self.category,
        }

        text_body = render_to_string('experts/email/expert_rejected.txt', context)
        html_body = render_to_string('experts/email/expert_rejected.html', context)

        email = EmailMultiAlternatives(subject, text_body, from_email, [recipient])
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=True)

    def send_approval_email(self):
        """Send an email to the user when their application is approved."""
        subject = 'You are now a verified expert on Youth of Nepal in Canada'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        recipient = self.user.email

        context = {
            'user': self.user,
            'category': self.category,
            'expert_profile_url': self.user.get_absolute_url() if hasattr(self.user, 'get_absolute_url') else None,
        }

        text_body = render_to_string('experts/email/expert_approved.txt', context)
        html_body = render_to_string('experts/email/expert_approved.html', context)

        email = EmailMultiAlternatives(subject, text_body, from_email, [recipient])
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=True)


class ExpertExperience(models.Model):
    """Professional experience entries for experts."""

    expert = models.ForeignKey(
        ExpertProfile,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-end_date']

    def __str__(self):
        return f"{self.title} at {self.company}"

    def get_date_range(self):
        start_label = self.start_date.strftime('%b %Y')
        if self.is_current or not self.end_date:
            return f"{start_label} – Present"
        return f"{start_label} – {self.end_date.strftime('%b %Y')}"
