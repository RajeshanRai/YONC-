from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from experts.models import ExpertProfile
from messaging.models import Message
from services.models import ServiceCategory
from .forms import EmailVerificationForm, UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
from .models import EmailVerificationCode, User, PendingUserRegistration


def _is_admin_user(user):
    return user.is_authenticated and user.is_admin()


def send_verification_email(request, email, code):
    subject = 'Your Youth of Nepal in Canada verification code'
    
    # Render HTML version
    html_body = render_to_string('accounts/email/verification_email.html', {
        'email': email,
        'code': code,
        'expiration_minutes': PendingUserRegistration.EXPIRATION_MINUTES,
    })
    
    # Render plain text fallback
    text_body = render_to_string('accounts/email/verification_email.txt', {
        'email': email,
        'code': code,
        'expiration_minutes': PendingUserRegistration.EXPIRATION_MINUTES,
    })
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    
    # Send email with both plain text and HTML
    msg = EmailMultiAlternatives(subject, text_body, from_email, [email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def home_view(request):
    """Landing page with province selector and featured experts."""
    context = {
        'provinces': User.PROVINCE_CHOICES,
        'service_categories': ServiceCategory.objects.all(),
        'featured_experts': ExpertProfile.objects.filter(
            is_approved=True, 
            is_featured=True
        ).select_related('user')[:6],
        'total_experts': ExpertProfile.objects.filter(is_approved=True).count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_categories': ServiceCategory.objects.count(),
    }
    return render(request, 'home.html', context)


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            
            # Clean up ALL expired pending registrations first
            PendingUserRegistration.objects.cleanup_expired()
            
            # Delete any existing pending registrations for this email/username
            # (allows retry if previous registration expired)
            PendingUserRegistration.objects.filter(email=email).delete()
            PendingUserRegistration.objects.filter(username=username).delete()
            
            # Generate verification code and create pending registration
            code = PendingUserRegistration.generate_code()
            pending = PendingUserRegistration.objects.create(
                email=email,
                username=username,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password1'],  # Already hashed by form
                province=form.cleaned_data.get('province'),
                city=form.cleaned_data.get('city'),
                phone_number=form.cleaned_data.get('phone_number'),
                verification_code=code,
            )
            
            # Send verification email
            send_verification_email(request, email, code)
            messages.success(request, 'Your account has been created. Enter the code we sent to your email to verify your account.')
            return redirect(f"{reverse('verify_email')}?email={email}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'title': 'Join YONC',
        'provinces': User.PROVINCE_CHOICES,
    })


def verification_sent_view(request):
    return render(request, 'accounts/verification_sent.html', {
        'title': 'Verify Your Email'
    })


def verify_email_view(request):
    email = request.GET.get('email', '') if request.method == 'GET' else request.POST.get('email', '')
    countdown_seconds = None

    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = form.cleaned_data['verification_code']
            
            try:
                pending = PendingUserRegistration.objects.get(email=email)
            except PendingUserRegistration.DoesNotExist:
                messages.error(request, 'No pending registration found with that email.')
            else:
                if pending.is_expired():
                    pending.delete()
                    messages.error(request, 'Your verification code has expired. Please register again.')
                    return redirect('register')
                
                if pending.verification_code != code:
                    messages.error(request, 'The verification code is invalid. Please check your email.')
                else:
                    # Create the actual user account
                    user = User.objects.create_user(
                        username=pending.username,
                        email=pending.email,
                        password=pending.password,
                        first_name=pending.first_name,
                        last_name=pending.last_name,
                        province=pending.province,
                        city=pending.city,
                        phone_number=pending.phone_number,
                        is_active=True,  # User is now active after verification
                    )
                    
                    # Clean up the pending registration
                    pending.delete()
                    
                    messages.success(request, 'Your email has been verified. You can now log in.')
                    return redirect('login')
        else:
            countdown_seconds = 0
    else:
        form = EmailVerificationForm(initial={'email': email})

    if email:
        try:
            pending = PendingUserRegistration.objects.get(email=email)
        except PendingUserRegistration.DoesNotExist:
            pending = None
        else:
            if pending.is_valid():
                countdown_seconds = pending.remaining_seconds()

    return render(request, 'accounts/verify_email.html', {
        'form': form,
        'title': 'Verify Your Email',
        'countdown_seconds': countdown_seconds,
    })


def resend_verification_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Clean up expired pending registrations
        PendingUserRegistration.objects.cleanup_expired()
        
        try:
            pending = PendingUserRegistration.objects.get(email=email)
            
            if pending.is_expired():
                pending.delete()
                messages.error(request, 'Your registration has expired. Please register again.')
                return redirect('register')
            
            # Generate new code and send
            code = PendingUserRegistration.generate_code()
            pending.verification_code = code
            pending.save()
            
            send_verification_email(request, email, code)
            messages.success(request, 'A new verification code has been sent. Enter it below to verify your account.')
            return redirect(f"{reverse('verify_email')}?email={email}")
        
        except PendingUserRegistration.DoesNotExist:
            # Check if user already exists and is verified
            try:
                user = User.objects.get(email=email)
                messages.info(request, 'This account is already verified. You can log in.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No pending registration found with that email.')

    return render(request, 'accounts/resend_verification.html', {
        'title': 'Resend Verification Code'
    })


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('home')

    login_error = None
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            login_error = 'Invalid username or password.'
        else:
            username = request.POST.get('username', '').strip()
            blocked_user = User.objects.filter(
                username=username,
                is_blocked_for_chat_violations=True,
            ).first()
            if blocked_user:
                login_error = 'Your account is blocked due to repeated spam/hate/bullying violations.'
                return render(request, 'accounts/login.html', {
                    'form': form,
                    'title': 'Sign In',
                    'login_error': login_error,
                })

            if form.errors.get('__all__'):
                login_error = form.errors['__all__'][0]
            else:
                login_error = 'Invalid username or password.'
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'title': 'Sign In',
        'login_error': login_error,
    })


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    """Display current user's profile."""
    user = request.user
    expert_profile = None
    
    if user.is_expert():
        expert_profile = ExpertProfile.objects.filter(user=user).first()
    
    context = {
        'profile_user': user,
        'expert_profile': expert_profile,
        'messages_count': Message.objects.filter(receiver=user, is_read=False).count(),
        'title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    """Edit current user's profile."""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'title': 'Edit Profile'
    })


def public_profile_view(request, pk):
    """View another user's public profile."""
    user = get_object_or_404(User, pk=pk, is_active=True)
    expert_profile = None
    
    if user.is_expert():
        expert_profile = ExpertProfile.objects.filter(user=user, is_approved=True).first()
    
    context = {
        'profile_user': user,
        'expert_profile': expert_profile,
        'title': f"{user.get_full_name_display()}'s Profile"
    }
    return render(request, 'accounts/public_profile.html', context)


@login_required
@require_POST
def mark_messages_read(request):
    """AJAX endpoint to mark all messages as read."""
    Message.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required
@user_passes_test(_is_admin_user)
def moderation_dashboard_view(request):
    """Admin moderation dashboard for violation monitoring and account unblocking."""
    status = request.GET.get('status', 'all')
    min_violations_raw = request.GET.get('min_violations', '1')
    page_number = request.GET.get('page', '1')

    try:
        min_violations = int(min_violations_raw)
    except (TypeError, ValueError):
        min_violations = 1
    min_violations = max(0, min_violations)

    users_qs = User.objects.filter(
        chat_violation_count__gte=min_violations,
    )

    if status == 'blocked':
        users_qs = users_qs.filter(is_blocked_for_chat_violations=True)
    elif status == 'active':
        users_qs = users_qs.filter(is_blocked_for_chat_violations=False)
    else:
        status = 'all'

    users_qs = users_qs.order_by('-is_blocked_for_chat_violations', '-chat_violation_count', 'username')
    paginator = Paginator(users_qs, 10)
    users = paginator.get_page(page_number)

    blocked_users = User.objects.filter(is_blocked_for_chat_violations=True).count()

    context = {
        'users': users,
        'total_users': users_qs.count(),
        'blocked_users': blocked_users,
        'status_filter': status,
        'min_violations_filter': min_violations,
        'title': 'Chat Moderation Dashboard',
    }
    return render(request, 'accounts/moderation_dashboard.html', context)


@login_required
@user_passes_test(_is_admin_user)
@require_POST
def unblock_moderated_user_view(request, pk):
    """Manually unblock a user that was blocked by chat moderation policy."""
    user = get_object_or_404(User, pk=pk)

    user.is_active = True
    user.is_blocked_for_chat_violations = False
    user.chat_blocked_at = None
    user.chat_violation_count = 0
    user.save(update_fields=[
        'is_active',
        'is_blocked_for_chat_violations',
        'chat_blocked_at',
        'chat_violation_count',
    ])

    messages.success(request, f'{user.username} has been unblocked and violation count reset.')
    return redirect('moderation_dashboard')
