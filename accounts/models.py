from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
import datetime
import random


class User(AbstractUser):
    """Custom User model with role-based access control."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('expert', 'Expert'),
        ('user', 'End User'),
    ]
    
    PROVINCE_CHOICES = [
        ('ON', 'Ontario'),
        ('BC', 'British Columbia'),
        ('AB', 'Alberta'),
        ('QC', 'Quebec'),
        ('MB', 'Manitoba'),
        ('SK', 'Saskatchewan'),
        ('NS', 'Nova Scotia'),
        ('NB', 'New Brunswick'),
        ('NL', 'Newfoundland and Labrador'),
        ('PE', 'Prince Edward Island'),
        ('NT', 'Northwest Territories'),
        ('YT', 'Yukon'),
        ('NU', 'Nunavut'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.png')
    bio = models.TextField(max_length=500, blank=True, null=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    def is_expert(self):
        return self.role == 'expert'
    
    def is_end_user(self):
        return self.role == 'user'
    
    def get_full_name_display(self):
        return self.get_full_name() or self.username
    
    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-avatar.png'


class UserProfile(models.Model):
    """Extended profile information for all users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    interests = models.TextField(max_length=500, blank=True, null=True)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'pk': self.user.pk})


class EmailVerificationCode(models.Model):
    EXPIRATION_MINUTES = 1

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Email verification code for {self.user.email}"

    @staticmethod
    def generate_code():
        return f"{random.randint(100000, 999999)}"

    def mark_as_used(self):
        self.is_active = False
        self.save()

    def expiration_time(self):
        return self.created_at + datetime.timedelta(minutes=self.EXPIRATION_MINUTES)

    def remaining_seconds(self):
        remaining = self.expiration_time() - timezone.now()
        return max(int(remaining.total_seconds()), 0)

    def is_expired(self):
        return self.remaining_seconds() <= 0

    def is_valid(self):
        return self.is_active and not self.is_expired()


class PendingUserRegistrationManager(models.Manager):
    """Manager for PendingUserRegistration to filter only valid registrations."""
    
    def valid(self):
        """Return only non-expired, non-used registrations."""
        from django.utils import timezone
        expiration_time_threshold = timezone.now() - datetime.timedelta(minutes=PendingUserRegistration.EXPIRATION_MINUTES)
        return self.filter(is_used=False, created_at__gte=expiration_time_threshold)
    
    def cleanup_expired(self):
        """Delete all expired registrations."""
        from django.utils import timezone
        expiration_time_threshold = timezone.now() - datetime.timedelta(minutes=PendingUserRegistration.EXPIRATION_MINUTES)
        return self.filter(is_used=False, created_at__lt=expiration_time_threshold).delete()


class PendingUserRegistration(models.Model):
    """Temporary storage for user registration data pending email verification."""
    
    EXPIRATION_MINUTES = 60  # Registration token valid for 60 minutes
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=255)  # Already hashed by form
    province = models.CharField(max_length=2, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    objects = PendingUserRegistrationManager()
    
    def __str__(self):
        return f"Pending registration: {self.email}"
    
    @staticmethod
    def generate_code():
        return f"{random.randint(100000, 999999)}"
    
    def expiration_time(self):
        return self.created_at + datetime.timedelta(minutes=self.EXPIRATION_MINUTES)
    
    def remaining_seconds(self):
        remaining = self.expiration_time() - timezone.now()
        return max(int(remaining.total_seconds()), 0)
    
    def is_expired(self):
        return self.remaining_seconds() <= 0
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()

