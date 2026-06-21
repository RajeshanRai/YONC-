from django import forms


class ResumeCoverLetterForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    phone = forms.CharField(max_length=40)
    location = forms.CharField(max_length=120)

    education = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    experience_summary = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), required=False)
    skills = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), help_text='Comma-separated skills, tools, or technologies.')
    achievements = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    certifications = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text='Certificates, licenses, or training.')
    projects = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text='Optional projects, portfolio items, or case studies.')
    languages = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, help_text='Languages you can speak or write.')
    references = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text='Reference names and contact details, or write "Available upon request".')
    additional_information = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text='Anything else that improves the resume, such as volunteer work or availability.')

    job_title = forms.CharField(max_length=120)
    company_name = forms.CharField(max_length=120, required=False)
    job_description = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}))

    tone = forms.ChoiceField(
        choices=[
            ('professional', 'Professional'),
            ('friendly', 'Friendly'),
            ('confident', 'Confident'),
        ],
        initial='professional',
    )
