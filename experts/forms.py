from django import forms
from .models import ExpertProfile, ExpertApplication, ExpertExperience
from services.models import ServiceCategory


class ExpertApplicationForm(forms.ModelForm):
    """Form for users to apply to become an expert."""
    
    agree_guidelines = forms.BooleanField(
        required=True,
        label='I agree to the community guidelines and confirm that all information provided is accurate.',
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded border-subtle text-accent-blue focus:ring-accent-blue'})
    )
    
    class Meta:
        model = ExpertApplication
        fields = ['category', 'years_experience', 'bio', 'qualifications', 
                  'specialties', 'phone_number', 'province', 'city']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'years_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'min': 0,
                'max': 60
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'rows': 5,
                'placeholder': 'Tell us about yourself, your background, and how you can help the community...'
            }),
            'qualifications': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'rows': 3,
                'placeholder': 'Education, certifications, degrees...'
            }),
            'specialties': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': 'e.g., Tax Filing, Web Development, Immigration Law (comma-separated)'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': '+1 (555) 123-4567'
            }),
            'province': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': 'e.g., Toronto, Vancouver, Calgary'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.filter(is_active=True)


class ExpertProfileUpdateForm(forms.ModelForm):
    """Form for experts to update their profile."""
    
    class Meta:
        model = ExpertProfile
        fields = ['category', 'years_experience', 'bio', 'qualifications', 
                  'specialties', 'phone_number', 'email_public', 'website',
                  'province', 'city', 'is_available', 'available_hours']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'years_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'min': 0
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'rows': 5
            }),
            'qualifications': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'rows': 3
            }),
            'specialties': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': 'Comma-separated specialties'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'email_public': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'province': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-subtle text-accent-blue focus:ring-accent-blue'
            }),
            'available_hours': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'placeholder': 'e.g., Mon-Fri 9AM-5PM EST'
            }),
        }


class ExpertExperienceForm(forms.ModelForm):
    """Form for experts to add their professional experience."""

    class Meta:
        model = ExpertExperience
        fields = ['company', 'title', 'start_date', 'end_date', 'is_current', 'description']
        widgets = {
            'company': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-subtle text-accent-blue focus:ring-accent-blue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue',
                'rows': 4
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')

        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('End date must be later than start date.')
        if is_current:
            cleaned_data['end_date'] = None
        return cleaned_data


class ExpertSearchForm(forms.Form):
    """Form for searching/filtering experts."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary placeholder-muted focus:outline-none focus:border-accent-blue transition-colors',
            'placeholder': 'Search by name, specialty, or keyword...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
        })
    )
    province = forms.ChoiceField(
        choices=[('', 'All Provinces')] + [
            ('ON', 'Ontario'), ('BC', 'British Columbia'), ('AB', 'Alberta'), ('QC', 'Quebec'),
            ('MB', 'Manitoba'), ('SK', 'Saskatchewan'), ('NS', 'Nova Scotia'), ('NB', 'New Brunswick'),
            ('NL', 'Newfoundland and Labrador'), ('PE', 'Prince Edward Island'),
            ('NT', 'Northwest Territories'), ('YT', 'Yukon'), ('NU', 'Nunavut'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary focus:outline-none focus:border-accent-blue'
        })
    )
