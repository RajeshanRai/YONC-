from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'image',
            'start_time',
            'end_time',
            'location',
            'is_online',
            'is_ticketed',
            'price',
            'total_seats',
            'registration_url',
            'is_featured',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
