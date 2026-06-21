from django.db import models
from django.conf import settings
from django.urls import reverse
import os


class ChatGroup(models.Model):
    """Professional chat group/channel for discussion."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_chat_groups'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMember',
        related_name='chat_groups'
    )
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('professional_chat:chat_group_detail', kwargs={'pk': self.pk})

    def add_member(self, user):
        """Add a user to the group."""
        GroupMember.objects.get_or_create(group=self, user=user)

    def remove_member(self, user):
        """Remove a user from the group."""
        GroupMember.objects.filter(group=self, user=user).delete()

    def is_member(self, user):
        """Check if user is a member."""
        return self.members.filter(pk=user.pk).exists()


class GroupMember(models.Model):
    """Track group membership and roles."""
    ROLE_ADMIN = 'admin'
    ROLE_MODERATOR = 'moderator'
    ROLE_MEMBER = 'member'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MODERATOR, 'Moderator'),
        (ROLE_MEMBER, 'Member'),
    ]

    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['group', 'user']

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class ChatMessage(models.Model):
    """Individual messages in a group."""
    group = models.ForeignKey(
        ChatGroup,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    content = models.TextField(blank=True, default='')
    attachment = models.FileField(upload_to='chat_attachments/groups/', blank=True, null=True)
    is_flagged = models.BooleanField(default=False, help_text='Flagged for toxicity')
    toxicity_score = models.FloatField(default=0.0, help_text='0-1 toxicity score from AI')
    toxicity_reason = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('hate_speech', 'Hate Speech'),
            ('bullying', 'Bullying'),
            ('spam', 'Spam'),
            ('other', 'Other Toxicity'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.username} in {self.group.name}"

    def get_display_name(self):
        return self.sender.get_full_name_display() or self.sender.username

    def get_avatar(self):
        if self.sender.profile_picture and self.sender.profile_picture.url != '/media/':
            return self.sender.profile_picture.url
        return None

    def get_initials(self):
        name = self.sender.get_full_name() or self.sender.username
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return name[:2].upper()

    def has_attachment(self):
        return bool(self.attachment)

    def get_attachment_name(self):
        if not self.attachment:
            return ''
        return os.path.basename(self.attachment.name)
