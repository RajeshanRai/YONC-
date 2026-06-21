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
    days_of_week = forms.MultipleChoiceField(
        choices=TimeSlot.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'grid grid-cols-2 gap-2'}),
        required=False,
        label='Days of Week',
        help_text='Select the weekdays when this slot is available.',
    )

    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time', 'capacity', 'discussion_topic', 'meeting_link', 'days_of_week']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-input'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-input'},
                format='%Y-%m-%dT%H:%M'
            ),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'step': 1,
            }),
            'discussion_topic': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Topic or purpose for this slot',
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'Zoom, Teams, or meeting URL',
            }),
        }
        labels = {
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'capacity': 'Capacity',
            'discussion_topic': 'Discussion Topic',
            'meeting_link': 'Meeting Link',
            'days_of_week': 'Days of Week',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']
        if self.instance and self.instance.pk and self.instance.days_of_week:
            self.initial['days_of_week'] = self.instance.days_of_week.split(',')

    def clean_days_of_week(self):
        days = self.cleaned_data.get('days_of_week', [])
        return ','.join(days)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('End time must be after start time.')
        capacity = cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError('Capacity must be at least 1.')
        return cleaned_data
