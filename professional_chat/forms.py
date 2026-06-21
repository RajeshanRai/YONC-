from django import forms
from .models import ChatGroup, ChatMessage


class ChatGroupForm(forms.ModelForm):
    """Form for creating and editing chat groups."""
    class Meta:
        model = ChatGroup
        fields = ['name', 'description', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Group name (e.g., Technology Experts)',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What is this group about?',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Group Name',
            'description': 'Description',
            'is_public': 'Make this group public',
        }


class ChatMessageForm(forms.ModelForm):
    """Form for sending messages."""
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control message-input',
                'rows': 2,
                'placeholder': 'Type your message...',
                'id': 'messageInput',
            }),
        }
        labels = {
            'content': '',
        }
