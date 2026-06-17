from django import forms

from .models import Appointment, TimeSlot


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['subject', 'notes']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'What would you like to discuss?'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Optional notes for the expert...'
            }),
        }
        labels = {
            'subject': 'Consultation topic',
            'notes': 'Additional notes',
        }


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-input'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-input'},
                format='%Y-%m-%dT%H:%M'
            ),
        }
        labels = {
            'start_time': 'Start Time',
            'end_time': 'End Time',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned_data
