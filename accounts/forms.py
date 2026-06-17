from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """Form for new user registration."""
    
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    province = forms.ChoiceField(choices=User.PROVINCE_CHOICES, required=True)
    city = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 
                  'province', 'city', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='w-1/2 pr-2'),
                Column('last_name', css_class='w-1/2 pl-2'),
                css_class='flex'
            ),
            'username',
            'email',
            'phone_number',
            Row(
                Column('province', css_class='w-1/2 pr-2'),
                Column('city', css_class='w-1/2 pl-2'),
                css_class='flex'
            ),
            'password1',
            'password2',
            Div(
                Submit('submit', 'Create Account', css_class='w-full bg-accent-blue hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all'),
                css_class='pt-4'
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        from .models import PendingUserRegistration
        
        # Clean up expired pending registrations
        PendingUserRegistration.objects.cleanup_expired()
        
        # Check if email already exists in User table
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        
        # Check if email already exists in valid pending registrations
        if PendingUserRegistration.objects.valid().filter(email=email).exists():
            raise forms.ValidationError('This email is already pending verification. Please check your inbox or request a new code.')
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data['username']
        from .models import PendingUserRegistration
        
        # Clean up expired pending registrations
        PendingUserRegistration.objects.cleanup_expired()
        
        # Check if username already exists in User table
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        
        # Check if username already exists in valid pending registrations
        if PendingUserRegistration.objects.valid().filter(username=username).exists():
            raise forms.ValidationError('This username is already pending verification.')
        
        return username


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(required=True)
    verification_code = forms.CharField(
        max_length=6,
        required=True,
        label='Verification Code',
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary placeholder-muted focus:outline-none focus:border-accent-blue transition-colors',
            'placeholder': 'Enter 6-digit code',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'email',
            'verification_code',
            Div(
                Submit('submit', 'Verify Email', css_class='w-full bg-accent-blue hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all'),
                css_class='pt-4'
            )
        )

    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError('Enter the 6-digit verification code from your email.')
        return code


class UserLoginForm(AuthenticationForm):
    """Form for user login."""
    
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary placeholder-muted focus:outline-none focus:border-accent-blue transition-colors',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control w-full px-4 py-3 rounded-lg bg-surface border border-subtle text-primary placeholder-muted focus:outline-none focus:border-accent-blue transition-colors',
        'placeholder': 'Password'
    }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'username',
            'password',
            Div(
                Submit('submit', 'Sign In', css_class='w-full bg-accent-blue hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all'),
                css_class='pt-4'
            )
        )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                'Please verify your email address before signing in.',
                code='inactive',
            )


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    province = forms.ChoiceField(choices=User.PROVINCE_CHOICES, required=False)
    city = forms.CharField(max_length=100, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                  'province', 'city', 'bio', 'profile_picture']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='w-1/2 pr-2'),
                Column('last_name', css_class='w-1/2 pl-2'),
                css_class='flex'
            ),
            'email',
            'phone_number',
            Row(
                Column('province', css_class='w-1/2 pr-2'),
                Column('city', css_class='w-1/2 pl-2'),
                css_class='flex'
            ),
            'bio',
            'profile_picture',
            Div(
                Submit('submit', 'Update Profile', css_class='bg-accent-blue hover:bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg transition-all'),
                css_class='pt-4'
            )
        )
