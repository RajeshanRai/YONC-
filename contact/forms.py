from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-bg-surface border border-border-subtle text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue transition-colors',
                'placeholder': 'Your Full Name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-bg-surface border border-border-subtle text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue transition-colors',
                'placeholder': 'Your Email Address',
                'required': True,
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-bg-surface border border-border-subtle text-text-primary focus:outline-none focus:border-accent-blue transition-colors',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-bg-surface border border-border-subtle text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue transition-colors resize-none',
                'placeholder': 'Tell us what you\'d like to discuss...',
                'rows': 6,
                'required': True,
            }),
        }
