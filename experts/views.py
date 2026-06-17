from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from accounts.models import User
from messaging.models import Conversation, Message
from services.models import ServiceCategory
from community.models import ForumPost, ForumComment
from appointments.forms import TimeSlotForm
from appointments.models import TimeSlot
from .models import ExpertProfile, ExpertApplication, ExpertExperience
from .forms import ExpertApplicationForm, ExpertProfileUpdateForm, ExpertExperienceForm, ExpertSearchForm


def expert_list(request):
    """List all approved experts with filtering."""
    form = ExpertSearchForm(request.GET or None)
    experts = ExpertProfile.objects.filter(is_approved=True).select_related('user', 'category')
    
    # Province filter
    province = request.GET.get('province')
    if province:
        experts = experts.filter(province=province)
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        experts = experts.filter(category__slug=category_slug)
    
    # Search filter
    search = request.GET.get('search')
    if search:
        experts = experts.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(bio__icontains=search) |
            Q(specialties__icontains=search) |
            Q(city__icontains=search)
        )
    
    # Ordering
    order = request.GET.get('order', '-rating')
    experts = experts.order_by('-is_featured', order)
    
    # Pagination
    paginator = Paginator(experts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Top picks
    top_picks = ExpertProfile.objects.filter(is_approved=True, is_featured=True).select_related('user', 'category')[:3]
    
    context = {
        'form': form,
        'experts': page_obj,
        'top_picks': top_picks,
        'categories': ServiceCategory.objects.filter(is_active=True),
        'provinces': User.PROVINCE_CHOICES,
        'title': 'Find an Expert',
        'total_count': experts.count(),
    }
    return render(request, 'experts/expert_list.html', context)


def expert_list_by_category(request, category_slug):
    """List experts filtered by category."""
    category = get_object_or_404(ServiceCategory, slug=category_slug, is_active=True)
    experts = ExpertProfile.objects.filter(
        category=category, 
        is_approved=True
    ).select_related('user', 'category').order_by('-is_featured', '-rating')
    
    paginator = Paginator(experts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'experts': page_obj,
        'categories': ServiceCategory.objects.filter(is_active=True),
        'provinces': User.PROVINCE_CHOICES,
        'title': f'{category.name} Experts',
        'total_count': experts.count(),
    }
    return render(request, 'experts/expert_list.html', context)


def expert_list_by_province(request, province_code):
    """List experts filtered by province."""
    province_names = dict(User.PROVINCE_CHOICES)
    province_name = province_names.get(province_code, province_code)
    
    experts = ExpertProfile.objects.filter(
        province=province_code, 
        is_approved=True
    ).select_related('user', 'category').order_by('-is_featured', '-rating')
    
    paginator = Paginator(experts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'province_code': province_code,
        'province_name': province_name,
        'experts': page_obj,
        'categories': ServiceCategory.objects.filter(is_active=True),
        'provinces': User.PROVINCE_CHOICES,
        'title': f'Experts in {province_name}',
        'total_count': experts.count(),
    }
    return render(request, 'experts/expert_list.html', context)


def expert_detail(request, pk):
    """Display detailed expert profile."""
    expert = get_object_or_404(
        ExpertProfile.objects.select_related('user', 'category').prefetch_related('experiences'),
        pk=pk,
        is_approved=True
    )
    
    experiences = expert.experiences.all()
    available_slots_qs = expert.time_slots.filter(is_booked=False, start_time__gte=timezone.now()).order_by('start_time')
    available_slots = available_slots_qs[:4]
    available_slots_count = available_slots_qs.count()
    next_available_slot = available_slots_qs.first()
    
    # Related experts
    related_experts = ExpertProfile.objects.filter(
        category=expert.category,
        is_approved=True
    ).exclude(pk=pk).select_related('user', 'category')[:4]
    
    # Check if user has chatted with this expert
    has_conversation = False
    if request.user.is_authenticated:
        has_conversation = Message.objects.filter(
            Q(sender=request.user, receiver=expert.user) |
            Q(sender=expert.user, receiver=request.user)
        ).exists()
    
    context = {
        'expert': expert,
        'experiences': experiences,
        'available_slots': available_slots,
        'available_slots_count': available_slots_count,
        'next_available_slot': next_available_slot,
        'related_experts': related_experts,
        'has_conversation': has_conversation,
        'title': f'{expert.user.get_full_name_display()} - {expert.category.name}',
    }
    return render(request, 'experts/expert_detail.html', context)


@login_required
def apply_expert(request):
    """Handle expert application submission."""
    # Check if user already has an expert profile
    if hasattr(request.user, 'expert_profile') and request.user.expert_profile.is_approved:
        messages.info(request, 'You are already an approved expert!')
        return redirect('expert_detail', pk=request.user.expert_profile.pk)
    
    # Check for pending application
    pending_app = ExpertApplication.objects.filter(user=request.user, status='pending').first()
    if pending_app:
        messages.info(request, 'You already have a pending application. Please wait for admin review.')
        return render(request, 'experts/application_status.html', {'application': pending_app})
    
    if request.method == 'POST':
        form = ExpertApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            messages.success(request, 'Your application has been submitted! An admin will review it shortly.')
            return render(request, 'experts/application_status.html', {'application': application})
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill with user data
        initial = {}
        if request.user.province:
            initial['province'] = request.user.province
        if request.user.city:
            initial['city'] = request.user.city
        if request.user.phone_number:
            initial['phone_number'] = request.user.phone_number
        form = ExpertApplicationForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Apply to be an Expert',
        'categories': ServiceCategory.objects.filter(is_active=True),
    }
    return render(request, 'experts/apply_expert.html', context)


@login_required
def expert_dashboard(request):
    """Expert's own dashboard."""
    if not request.user.is_expert():
        messages.error(request, 'Access denied. Only experts can view this page.')
        return redirect('home')
    
    expert = get_object_or_404(ExpertProfile, user=request.user)
    
    # Stats
    unread_messages = Message.objects.filter(receiver=request.user, is_read=False).count()
    total_conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).count()
    
    # Recent conversation summaries
    recent_conversations = Conversation.objects.filter(
        (Q(participant1=request.user) | Q(participant2=request.user)) &
        Q(last_message__isnull=False)
    ).select_related('participant1', 'participant2', 'last_message').order_by('-updated_at')[:10]
    
    recent_conversation_items = []
    for conversation in recent_conversations:
        other_user = conversation.get_other_participant(request.user)
        last_message = conversation.last_message
        recent_conversation_items.append({
            'conversation': conversation,
            'other_user': other_user,
            'last_message': last_message,
        })
    
    forum_posts_count = ForumPost.objects.filter(is_active=True).count()
    forum_comments_count = ForumComment.objects.filter(is_active=True).count()
    recent_forum_posts = ForumPost.objects.filter(is_active=True).select_related('author', 'category')[:5]

    upcoming_slots_count = TimeSlot.objects.filter(
        expert=expert,
        start_time__gte=timezone.now(),
        is_booked=False
    ).count()
    experience_count = ExpertExperience.objects.filter(expert=expert).count()

    context = {
        'expert': expert,
        'unread_messages': unread_messages,
        'total_conversations': total_conversations,
        'recent_conversations': recent_conversation_items,
        'forum_posts_count': forum_posts_count,
        'forum_comments_count': forum_comments_count,
        'recent_forum_posts': recent_forum_posts,
        'upcoming_slots_count': upcoming_slots_count,
        'experience_count': experience_count,
        'title': 'Expert Dashboard',
    }
    return render(request, 'experts/expert_dashboard.html', context)


@login_required
def expert_availability(request):
    if not request.user.is_expert():
        messages.error(request, 'Access denied. Only experts can manage availability.')
        return redirect('home')

    expert = get_object_or_404(ExpertProfile, user=request.user)
    slots = TimeSlot.objects.filter(expert=expert).order_by('start_time')

    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.expert = expert
            slot.save()
            messages.success(request, 'Availability has been added to your schedule.')
            return redirect('expert_availability')
        else:
            messages.error(request, 'Please correct the form errors below.')
    else:
        form = TimeSlotForm()

    context = {
        'expert': expert,
        'form': form,
        'slots': slots,
        'title': 'Manage Availability',
    }
    return render(request, 'experts/expert_availability.html', context)


@login_required
def expert_experience(request):
    if not request.user.is_expert():
        messages.error(request, 'Access denied. Only experts can manage experience entries.')
        return redirect('home')

    expert = get_object_or_404(ExpertProfile, user=request.user)
    experiences = ExpertExperience.objects.filter(expert=expert).order_by('-start_date', '-end_date')

    if request.method == 'POST':
        form = ExpertExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.expert = expert
            experience.save()
            messages.success(request, 'Your experience entry has been saved.')
            return redirect('expert_experience')
        else:
            messages.error(request, 'Please correct the form errors below.')
    else:
        form = ExpertExperienceForm()

    # Calculate total experience and date ranges
    total_experience = expert.get_total_years_experience()
    earliest_date = None
    latest_date = None
    
    if experiences:
        earliest_date = experiences.last().start_date.strftime('%b %Y') if experiences else None
        latest_exp = experiences.first()
        latest_date = (latest_exp.end_date if latest_exp.end_date else timezone.now()).strftime('%b %Y')

    context = {
        'expert': expert,
        'experiences': experiences,
        'form': form,
        'title': 'Manage Experience',
        'total_experience': total_experience,
        'earliest_date': earliest_date,
        'latest_date': latest_date,
    }
    return render(request, 'experts/expert_experience.html', context)


@login_required
def expert_experience_delete(request, pk):
    if request.method != 'POST':
        return redirect('expert_experience')

    if not request.user.is_expert():
        messages.error(request, 'Access denied.')
        return redirect('home')

    expert = get_object_or_404(ExpertProfile, user=request.user)
    experience = get_object_or_404(ExpertExperience, pk=pk, expert=expert)
    experience.delete()
    messages.success(request, 'Experience entry removed successfully.')
    return redirect('expert_experience')


@login_required
def expert_availability_delete(request, pk):
    if request.method != 'POST':
        return redirect('expert_availability')

    if not request.user.is_expert():
        messages.error(request, 'Access denied.')
        return redirect('home')

    expert = get_object_or_404(ExpertProfile, user=request.user)
    slot = get_object_or_404(TimeSlot, pk=pk, expert=expert, is_booked=False)
    slot.delete()
    messages.success(request, 'The time slot has been removed from your availability list.')
    return redirect('expert_availability')


@login_required
def expert_profile_edit(request):
    """Edit expert profile."""
    if not request.user.is_expert():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    expert = get_object_or_404(ExpertProfile, user=request.user)
    
    if request.method == 'POST':
        form = ExpertProfileUpdateForm(request.POST, instance=expert)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your expert profile has been updated!')
            return redirect('expert_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExpertProfileUpdateForm(instance=expert)
    
    return render(request, 'experts/expert_profile_edit.html', {
        'form': form,
        'expert': expert,
        'title': 'Edit Expert Profile'
    })


@login_required
def application_status(request):
    """View application status."""
    application = ExpertApplication.objects.filter(user=request.user).order_by('-submitted_at').first()
    if not application:
        messages.info(request, 'You have not submitted any application yet.')
        return redirect('apply_expert')
    
    return render(request, 'experts/application_status.html', {
        'application': application,
        'title': 'Application Status'
    })
