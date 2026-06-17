from django import forms

from .models import ForumPost, ForumComment
from services.models import ServiceCategory


class ForumPostForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        empty_label='Select a category',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Choose the most relevant topic for your discussion.',
    )

    class Meta:
        model = ForumPost
        fields = ['category', 'title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter a clear question or discussion title'}),
            'content': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6, 'placeholder': 'Share your question or advice...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.filter(is_active=True)

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise forms.ValidationError('Please select a category.')
        if not ServiceCategory.objects.filter(pk=category.pk, is_active=True).exists():
            raise forms.ValidationError('The selected category is not available.')
        return category

class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Write your response...'}),
        }
