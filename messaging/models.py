from django.db import models
from django.conf import settings
from django.urls import reverse


class Message(models.Model):
    """One-to-one messaging between users."""
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['receiver', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    def get_timestamp_display(self):
        from django.utils import timezone
        now = timezone.now()
        diff = now - self.timestamp
        
        if diff.days == 0:
            if diff.seconds < 60:
                return 'Just now'
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f'{minutes}m ago'
            else:
                hours = diff.seconds // 3600
                return f'{hours}h ago'
        elif diff.days == 1:
            return 'Yesterday'
        elif diff.days < 7:
            return f'{diff.days}d ago'
        else:
            return self.timestamp.strftime('%b %d')


class Conversation(models.Model):
    """Helper model to track conversations between two users."""
    
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_p1'
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_p2'
    )
    last_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_last'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['participant1', 'participant2']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation: {self.participant1.username} - {self.participant2.username}"
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create a conversation between two users."""
        p1, p2 = sorted([user1, user2], key=lambda u: u.id)
        conversation, created = cls.objects.get_or_create(
            participant1=p1,
            participant2=p2
        )
        return conversation
    
    def get_other_participant(self, current_user):
        """Get the other participant in the conversation."""
        if current_user.id == self.participant1_id:
            return self.participant2
        return self.participant1
    
    def get_unread_count(self, user):
        """Get unread message count for a user in this conversation."""
        return Message.objects.filter(
            sender=self.get_other_participant(user),
            receiver=user,
            is_read=False
        ).count()
