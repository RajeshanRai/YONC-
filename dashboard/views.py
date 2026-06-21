from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from about.models import Partner
from about.forms import PartnerForm
from experts.models import ExpertProfile, ExpertApplication
from events.models import Event
from messaging.models import Message, Conversation
from services.models import ServiceCategory
from contact.models import ContactMessage
from professional_chat.models import ChatGroup, ChatMessage


def is_admin(user):
    """Check if user is admin."""
    return user.is_authenticated and user.is_admin()


@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    """Admin dashboard home with analytics."""
    today = timezone.now()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    
    # Key stats
    total_users = User.objects.filter(is_active=True).count()
    total_experts = ExpertProfile.objects.filter(is_approved=True).count()
    pending_applications = ExpertApplication.objects.filter(status='pending').count()
    total_messages_today = Message.objects.filter(timestamp__date=today.date()).count()
    
    # User growth (last 7 days)
    user_growth = User.objects.filter(
        is_active=True,
        date_joined__gte=last_7_days
    ).annotate(date=TruncDate('date_joined')).values('date').annotate(count=Count('id')).order_by('date')
    
    # Expert applications (last 7 days)
    applications_by_day = ExpertApplication.objects.filter(
        submitted_at__gte=last_7_days
    ).annotate(date=TruncDate('submitted_at')).values('date').annotate(count=Count('id')).order_by('date')
    
    # Messages (last 7 days)
    messages_by_day = Message.objects.filter(
        timestamp__gte=last_7_days
    ).annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('id')).order_by('date')
    
    # Category distribution
    category_stats = ServiceCategory.objects.annotate(
        expert_count=Count('expert_profiles', filter=Q(expert_profiles__is_approved=True))
    ).values('name', 'expert_count', 'color').order_by('-expert_count')
    
    # Province distribution
    province_stats = ExpertProfile.objects.filter(is_approved=True).values('province').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent activity
    recent_users = User.objects.filter(is_active=True).order_by('-date_joined')[:10]
    recent_applications = ExpertApplication.objects.select_related('user', 'category').order_by('-submitted_at')[:10]
    recent_messages = Message.objects.select_related('sender', 'receiver').order_by('-timestamp')[:10]
    
    context = {
        'title': 'Admin Dashboard',
        'stats': {
            'total_users': total_users,
            'total_experts': total_experts,
            'pending_applications': pending_applications,
            'total_messages_today': total_messages_today,
        },
        'user_growth': list(user_growth),
        'applications_by_day': list(applications_by_day),
        'messages_by_day': list(messages_by_day),
        'category_stats': list(category_stats),
        'province_stats': list(province_stats),
        'recent_users': recent_users,
        'recent_applications': recent_applications,
        'recent_messages': recent_messages,
    }
    return render(request, 'dashboard/dashboard_home.html', context)


@login_required
@user_passes_test(is_admin)
def manage_experts(request):
    """Manage all expert profiles."""
    status = request.GET.get('status', 'all')
    
    experts = ExpertProfile.objects.select_related('user', 'category').order_by('-created_at')
    
    if status == 'approved':
        experts = experts.filter(is_approved=True)
    elif status == 'pending':
        experts = experts.filter(is_approved=False)
    
    context = {
        'title': 'Manage Experts',
        'experts': experts,
        'status_filter': status,
        'total_count': experts.count(),
    }
    return render(request, 'dashboard/manage_experts.html', context)


@login_required
@user_passes_test(is_admin)
def manage_applications(request):
    """Review expert applications."""
    status = request.GET.get('status', 'pending')
    
    applications = ExpertApplication.objects.select_related('user', 'category').order_by('-submitted_at')
    
    if status != 'all':
        applications = applications.filter(status=status)
    
    context = {
        'title': 'Expert Applications',
        'applications': applications,
        'status_filter': status,
        'total_count': applications.count(),
    }
    return render(request, 'dashboard/manage_applications.html', context)


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """Manage all users."""
    role = request.GET.get('role', 'all')
    
    users = User.objects.order_by('-date_joined')
    
    if role != 'all':
        users = users.filter(role=role)
    
    context = {
        'title': 'Manage Users',
        'users': users,
        'role_filter': role,
        'total_count': users.count(),
    }
    return render(request, 'dashboard/manage_users.html', context)


@login_required
@user_passes_test(is_admin)
def manage_messages(request):
    """View conversations instead of every individual message."""
    conversations = Conversation.objects.select_related('participant1', 'participant2', 'last_message').all()

    conversation_rows = []
    for conv in conversations:
        other = None
        if conv.participant1.is_admin() and not conv.participant2.is_admin():
            other = conv.participant2
        elif conv.participant2.is_admin() and not conv.participant1.is_admin():
            other = conv.participant1
        else:
            # if both participants are admins or both not, just show the first participant as partner
            other = conv.participant2

        conversation_rows.append({
            'conversation': conv,
            'participant_a': conv.participant1,
            'participant_b': conv.participant2,
            'other': other,
            'last_message': conv.last_message,
            'unread_count': conv.get_unread_count(request.user),
        })

    # Stats
    total_messages = Message.objects.count()
    total_group_messages = ChatMessage.objects.count()
    messages_today = Message.objects.filter(timestamp__date=timezone.now().date()).count()
    unread_messages = Message.objects.filter(is_read=False).count()

    groups = ChatGroup.objects.all().order_by('name')
    group_rows = []
    for group in groups:
        group_rows.append({
            'group': group,
            'message_count': group.messages.count(),
            'members_count': group.members.count(),
            'last_message': group.messages.order_by('-created_at').first(),
        })
    
    context = {
        'title': 'Messages Overview',
        'conversations': conversation_rows,
        'stats': {
            'total': total_messages + total_group_messages,
            'direct_total': total_messages,
            'group_total': total_group_messages,
            'today': messages_today,
            'unread': unread_messages,
        },
        'group_rows': group_rows,
    }
    return render(request, 'dashboard/manage_messages.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_conversation_messages(request, conversation_id):
    """Delete all direct messages in a specific conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    Message.objects.filter(
        (Q(sender=conversation.participant1) & Q(receiver=conversation.participant2))
        | (Q(sender=conversation.participant2) & Q(receiver=conversation.participant1))
    ).delete()
    conversation.last_message = None
    conversation.save(update_fields=['last_message', 'updated_at'])
    messages.success(request, 'All messages in the selected conversation were deleted.')
    return redirect('manage_messages')


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_group_messages(request, group_id):
    """Delete all messages in a specific group."""
    group = get_object_or_404(ChatGroup, id=group_id)
    group.messages.all().delete()
    messages.success(request, f'All messages in group "{group.name}" were deleted.')
    return redirect('manage_messages')


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_group(request, group_id):
    """Delete an entire group and related messages/members."""
    group = get_object_or_404(ChatGroup, id=group_id)
    group_name = group.name
    group.delete()
    messages.success(request, f'Group "{group_name}" was deleted successfully.')
    return redirect('manage_messages')


@login_required
@user_passes_test(is_admin)
def manage_partners(request):
    """Manage active and inactive About partners."""
    status = request.GET.get('status', 'all')
    partners = Partner.objects.order_by('sort_order', 'name')

    if status == 'active':
        partners = partners.filter(is_active=True)
    elif status == 'inactive':
        partners = partners.filter(is_active=False)

    context = {
        'title': 'Manage Partners',
        'partners': partners,
        'status_filter': status,
        'total_count': partners.count(),
    }
    return render(request, 'dashboard/manage_partners.html', context)


@login_required
@user_passes_test(is_admin)
def create_partner(request):
    """Add a new partner from the admin dashboard."""
    if request.method == 'POST':
        form = PartnerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Partner added successfully.')
            return redirect('manage_partners')
    else:
        form = PartnerForm()

    return render(request, 'dashboard/partner_form.html', {
        'title': 'Add Partner',
        'form': form,
        'is_edit': False,
    })


@login_required
@user_passes_test(is_admin)
def manage_events(request):
    """Manage events from the admin dashboard."""
    events = Event.objects.order_by('start_time')
    context = {
        'title': 'Manage Events',
        'events': events,
        'total_count': events.count(),
    }
    return render(request, 'dashboard/manage_events.html', context)


@login_required
@user_passes_test(is_admin)
def create_event(request):
    from events.forms import EventForm

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event created successfully.')
            return redirect('manage_events')
    else:
        form = EventForm()

    return render(request, 'dashboard/event_form.html', {
        'title': 'Add Event',
        'form': form,
        'is_edit': False,
    })


@login_required
@user_passes_test(is_admin)
def edit_event(request, event_id):
    from events.forms import EventForm
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('manage_events')
    else:
        form = EventForm(instance=event)

    return render(request, 'dashboard/event_form.html', {
        'title': f'Edit Event: {event.title}',
        'form': form,
        'is_edit': True,
        'event': event,
    })


@login_required
@user_passes_test(is_admin)
def edit_partner(request, partner_id):
    """Edit an existing partner from the admin dashboard."""
    partner = get_object_or_404(Partner, id=partner_id)

    if request.method == 'POST':
        form = PartnerForm(request.POST, request.FILES, instance=partner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Partner updated successfully.')
            return redirect('manage_partners')
    else:
        form = PartnerForm(instance=partner)

    return render(request, 'dashboard/partner_form.html', {
        'title': f'Edit Partner: {partner.name}',
        'form': form,
        'is_edit': True,
        'partner': partner,
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_partner_active(request, partner_id):
    """Activate or deactivate a partner."""
    partner = get_object_or_404(Partner, id=partner_id)
    partner.is_active = not partner.is_active
    partner.save()

    status_text = 'activated' if partner.is_active else 'deactivated'
    return JsonResponse({
        'status': 'success',
        'is_active': partner.is_active,
        'message': f'Partner {partner.name} has been {status_text}.',
    })


# AJAX Actions

@login_required
@user_passes_test(is_admin)
@require_POST
def approve_application(request, app_id):
    """Approve an expert application."""
    application = get_object_or_404(ExpertApplication, id=app_id, status='pending')
    
    try:
        application.approve()
        messages.success(request, f'Application from {application.user.username} has been approved!')
        return JsonResponse({
            'status': 'success',
            'message': 'Application approved successfully',
            'expert_id': application.user.expert_profile.id if hasattr(application.user, 'expert_profile') else None
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_POST
def reject_application(request, app_id):
    """Reject an expert application."""
    application = get_object_or_404(ExpertApplication, id=app_id, status='pending')
    review_notes = request.POST.get('review_notes', '')
    
    try:
        application.status = 'rejected'
        application.review_notes = review_notes
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        messages.success(request, f'Application from {application.user.username} has been rejected.')
        return JsonResponse({'status': 'success', 'message': 'Application rejected'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_expert_featured(request, expert_id):
    """Toggle featured status for an expert."""
    expert = get_object_or_404(ExpertProfile, id=expert_id)
    expert.is_featured = not expert.is_featured
    expert.save()
    
    status_text = 'featured' if expert.is_featured else 'unfeatured'
    messages.success(request, f'Expert {expert.user.username} is now {status_text}.')
    
    return JsonResponse({
        'status': 'success',
        'is_featured': expert.is_featured,
        'message': f'Expert {status_text} successfully'
    })


@login_required
@user_passes_test(is_admin)
def manage_contacts(request):
    """List and manage ContactMessage submissions."""
    status = request.GET.get('status', 'all')

    contacts = ContactMessage.objects.order_by('-created_at')
    if status == 'unread':
        contacts = contacts.filter(is_read=False)
    elif status == 'replied':
        contacts = contacts.filter(replied=True)

    total = ContactMessage.objects.count()
    unread = ContactMessage.objects.filter(is_read=False).count()

    context = {
        'title': 'Manage Contacts',
        'contacts': contacts,
        'status_filter': status,
        'total_count': total,
        'stats': {
            'total': total,
            'unread': unread,
        },
    }
    return render(request, 'dashboard/manage_contacts.html', context)


@login_required
@user_passes_test(is_admin)
def contact_detail(request, contact_id):
    contact = get_object_or_404(ContactMessage, id=contact_id)
    if not contact.is_read:
        contact.is_read = True
        contact.save()

    return render(request, 'dashboard/contact_detail.html', {
        'title': 'Contact Detail',
        'contact': contact,
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_contact_read(request, contact_id):
    contact = get_object_or_404(ContactMessage, id=contact_id)
    contact.is_read = not contact.is_read
    contact.save()
    return JsonResponse({'status': 'success', 'is_read': contact.is_read})


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_contact_replied(request, contact_id):
    contact = get_object_or_404(ContactMessage, id=contact_id)
    contact.replied = not contact.replied
    contact.save()
    return JsonResponse({'status': 'success', 'replied': contact.replied})


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_contact(request, contact_id):
    contact = get_object_or_404(ContactMessage, id=contact_id)
    contact.delete()
    return JsonResponse({'status': 'success', 'deleted': True})


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_user(request, user_id):
    """Delete a user account."""
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot delete yourself'}, status=400)
    
    username = user.username
    user.delete()
    return JsonResponse({'status': 'success', 'deleted': True, 'message': f'User {username} deleted'})


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_user_active(request, user_id):
    """Activate/deactivate a user."""
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot deactivate yourself'}, status=400)
    
    user.is_active = not user.is_active
    user.save()
    
    status_text = 'activated' if user.is_active else 'deactivated'
    return JsonResponse({'status': 'success', 'is_active': user.is_active, 'message': f'User {status_text}'})


@login_required
@user_passes_test(is_admin)
def dashboard_stats_api(request):
    """API endpoint for dashboard charts."""
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    
    # Daily new users for the last 30 days
    daily_users = User.objects.filter(
        date_joined__gte=last_30_days
    ).annotate(date=TruncDate('date_joined')).values('date').annotate(count=Count('id')).order_by('date')
    
    # Daily messages
    daily_messages = Message.objects.filter(
        timestamp__gte=last_30_days
    ).annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('id')).order_by('date')
    
    # Daily applications
    daily_applications = ExpertApplication.objects.filter(
        submitted_at__gte=last_30_days
    ).annotate(date=TruncDate('submitted_at')).values('date').annotate(count=Count('id')).order_by('date')
    
    return JsonResponse({
        'status': 'success',
        'daily_users': list(daily_users),
        'daily_messages': list(daily_messages),
        'daily_applications': list(daily_applications),
    })
