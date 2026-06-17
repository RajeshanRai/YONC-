from django import forms

from .models import Partner


class PartnerForm(forms.ModelForm):
    """Form for creating and updating About partners."""

    class Meta:
        model = Partner
        fields = ['name', 'website', 'logo', 'description', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': 'Partner organization name'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': 'https://partner.example.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'rows': 4,
                'placeholder': 'A short description of the partner'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-subtle text-accent-blue focus:ring-accent-blue'
            }),
        }
