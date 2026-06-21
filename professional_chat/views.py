from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django.core import signing
from django.urls import reverse
from pathlib import Path
from accounts.models import User

from .models import ChatGroup, ChatMessage, GroupMember
from .forms import ChatGroupForm, ChatMessageForm
from .moderator import ContentModerator
from messaging.models import Conversation, Message


MAX_CHAT_VIOLATIONS = 10
PRIVATE_GROUP_INVITE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
INVITE_SALT = 'professional-chat-private-group-invite'
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_ATTACHMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx'}
ALLOWED_ATTACHMENT_CONTENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream',
}


def _handle_violation_attempt(user):
    """Increment violation count and block account when threshold is reached."""
    user.chat_violation_count = (user.chat_violation_count or 0) + 1
    violations_remaining = max(0, MAX_CHAT_VIOLATIONS - user.chat_violation_count)
    is_blocked = user.chat_violation_count >= MAX_CHAT_VIOLATIONS

    if is_blocked:
        user.is_active = False
        user.is_blocked_for_chat_violations = True
        user.chat_blocked_at = timezone.now()

    user.save(update_fields=[
        'chat_violation_count',
        'is_active',
        'is_blocked_for_chat_violations',
        'chat_blocked_at',
    ])

    if is_blocked:
        ChatMessage.objects.filter(sender=user).delete()

    return {
        'is_blocked': is_blocked,
        'violations_count': user.chat_violation_count,
        'violations_remaining': violations_remaining,
    }


def _is_group_admin(group, user):
    return user == group.created_by or GroupMember.objects.filter(
        group=group,
        user=user,
        role=GroupMember.ROLE_ADMIN,
    ).exists()


def _build_group_invite_token(group):
    payload = {
        'group_id': group.pk,
        'private': group.is_public is False,
    }
    return signing.dumps(payload, salt=INVITE_SALT)


def _chat_time_label(dt):
    return timezone.localtime(dt).strftime('%H:%M')


def _is_system_activity_message(message):
    return (
        bool(message)
        and (
            (message.content or '').strip().endswith('joined the chat')
            or (message.content or '').strip().endswith('left the group')
        )
        and not message.attachment
    )


def _add_member_and_announce(group, user):
    """Add a member and post a visible join announcement once."""
    membership, created = GroupMember.objects.get_or_create(group=group, user=user)
    if created:
        display_name = user.get_full_name_display() or user.username
        ChatMessage.objects.create(
            group=group,
            sender=user,
            content=f'{display_name} joined the chat',
            is_flagged=False,
            toxicity_score=0.0,
            toxicity_reason='',
        )
    return membership, created


def _validate_chat_attachment(uploaded_file):
    if not uploaded_file:
        return None

    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return 'Only PDF, Word, and Excel files are allowed.'

    content_type = (uploaded_file.content_type or '').lower()
    if content_type and content_type not in ALLOWED_ATTACHMENT_CONTENT_TYPES:
        return 'Only PDF, Word, and Excel files are allowed.'

    if uploaded_file.size > MAX_ATTACHMENT_SIZE_BYTES:
        return 'File too large. Maximum allowed size is 10 MB.'

    return None


@login_required
def chat_group_list(request):
    """List user chat groups and public joinable groups."""
    user_groups = request.user.chat_groups.prefetch_related('members')
    public_groups = ChatGroup.objects.filter(is_public=True).exclude(members=request.user).prefetch_related('members')
    can_create_group = request.user.is_admin() or request.user.is_expert()

    conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).select_related('participant1', 'participant2', 'last_message').order_by('-updated_at')[:8]

    direct_chats = []
    for conversation in conversations:
        other_user = conversation.get_other_participant(request.user)
        unread_count = conversation.get_unread_count(request.user)
        direct_chats.append({
            'other_user': other_user,
            'unread_count': unread_count,
            'last_message': conversation.last_message,
        })

    total_unread = Message.objects.filter(receiver=request.user, is_read=False).count()

    user_search = request.GET.get('user_search', '').strip()
    available_users = []
    min_search_length = 2

    if len(user_search) >= min_search_length:
        available_users_qs = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
        available_users_qs = available_users_qs.filter(
            Q(username__istartswith=user_search)
            | Q(first_name__istartswith=user_search)
            | Q(last_name__istartswith=user_search)
        )
        available_users = available_users_qs.order_by('first_name', 'last_name', 'username')[:10]

    context = {
        'user_groups': user_groups,
        'public_groups': public_groups,
        'can_create_group': can_create_group,
        'direct_chats': direct_chats,
        'total_unread': total_unread,
        'available_users': available_users,
        'user_search': user_search,
        'min_search_length': min_search_length,
        'title': 'Professional Chat Groups',
    }
    return render(request, 'professional_chat/group_list.html', context)


@login_required
def create_chat_group(request):
    """Create a new chat group."""
    if not (request.user.is_admin() or request.user.is_expert()):
        messages.error(request, 'Only administrators and verified experts can create professional chat groups.')
        return redirect('professional_chat:chat_group_list')

    if request.method == 'POST':
        form = ChatGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            GroupMember.objects.update_or_create(
                group=group,
                user=request.user,
                defaults={'role': GroupMember.ROLE_ADMIN},
            )
            messages.success(request, 'Chat group created successfully!')
            return redirect('professional_chat:chat_group_detail', pk=group.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChatGroupForm()
    
    context = {
        'form': form,
        'title': 'Create Chat Group',
    }
    return render(request, 'professional_chat/create_group.html', context)


@login_required
def chat_group_detail(request, pk):
    """Display chat room for a specific group."""
    group = get_object_or_404(ChatGroup, pk=pk)
    
    # Check if user is member or if it's public
    if not group.is_member(request.user) and not group.is_public:
        messages.error(request, 'You do not have access to this group.')
        return redirect('professional_chat:chat_group_list')
    
    # Auto-join if public and not member
    if not group.is_member(request.user) and group.is_public:
        _add_member_and_announce(group, request.user)

    membership = GroupMember.objects.filter(group=group, user=request.user).first()
    if membership is None:
        messages.error(request, 'You are not a member of this group.')
        return redirect('professional_chat:chat_group_list')

    messages_list = list(
        group.messages
        .select_related('sender')
        .filter(created_at__gte=membership.joined_at)
    )
    previous_sender_id = None
    for message in messages_list:
        message.is_system = _is_system_activity_message(message)
        if message.is_system:
            message.show_sender_name = False
            message.show_time_label = False
            previous_sender_id = None
            continue
        message.show_sender_name = message.sender_id != previous_sender_id
        message.show_time_label = message.show_sender_name
        previous_sender_id = message.sender_id
    form = ChatMessageForm()
    group_members = GroupMember.objects.filter(group=group).select_related('user').order_by('role', 'joined_at')
    members = group.members.all()
    is_group_admin = _is_group_admin(group, request.user)

    member_search = request.GET.get('member_search', '').strip()
    candidate_users = []
    invite_link = None

    if not group.is_public and is_group_admin:
        invite_token = _build_group_invite_token(group)
        invite_link = request.build_absolute_uri(
            reverse('professional_chat:join_private_group_with_token', kwargs={'token': invite_token})
        )

        candidate_users_qs = User.objects.filter(is_active=True).exclude(
            pk__in=group.members.values_list('pk', flat=True)
        )
        if member_search:
            candidate_users_qs = candidate_users_qs.filter(
                Q(username__istartswith=member_search)
                | Q(first_name__istartswith=member_search)
                | Q(last_name__istartswith=member_search)
            )

        candidate_users = candidate_users_qs.order_by('first_name', 'last_name', 'username')[:10]
    
    context = {
        'group': group,
        'chat_messages': messages_list,
        'form': form,
        'members': members,
        'group_members': group_members,
        'is_group_admin': is_group_admin,
        'can_delete_group': request.user == group.created_by or request.user.is_admin(),
        'invite_link': invite_link,
        'candidate_users': candidate_users,
        'member_search': member_search,
        'title': f'{group.name} - Chat',
    }
    return render(request, 'professional_chat/chat_room.html', context)


@login_required
def join_private_group_with_token(request, token):
    """Join a private group using a signed invite token."""
    try:
        data = signing.loads(
            token,
            salt=INVITE_SALT,
            max_age=PRIVATE_GROUP_INVITE_MAX_AGE_SECONDS,
        )
        group_id = data.get('group_id')
    except signing.BadSignature:
        messages.error(request, 'Invalid invite link.')
        return redirect('professional_chat:chat_group_list')
    except signing.SignatureExpired:
        messages.error(request, 'Invite link has expired.')
        return redirect('professional_chat:chat_group_list')

    group = get_object_or_404(ChatGroup, pk=group_id)
    if group.is_public:
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if not group.is_member(request.user):
        _add_member_and_announce(group, request.user)
        messages.success(request, f'You have joined {group.name}.')

    return redirect('professional_chat:chat_group_detail', pk=group.pk)


@login_required
@require_POST
def add_private_group_member(request, pk):
    """Allow private-group admins to add users manually."""
    group = get_object_or_404(ChatGroup, pk=pk)

    if group.is_public:
        messages.error(request, 'Manual member add is only available for private groups.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if not _is_group_admin(group, request.user):
        messages.error(request, 'Only group admins can add members to private groups.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    user_id = request.POST.get('user_id')
    if not user_id:
        messages.error(request, 'Please select a user to add.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    user_to_add = get_object_or_404(User, pk=user_id, is_active=True)
    if group.is_member(user_to_add):
        messages.info(request, f'{user_to_add.get_full_name_display()} is already in this group.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    _add_member_and_announce(group, user_to_add)
    messages.success(request, f'{user_to_add.get_full_name_display()} has been added to {group.name}.')
    return redirect('professional_chat:chat_group_detail', pk=group.pk)


@login_required
@require_POST
def promote_group_member_to_moderator(request, pk, user_id):
    """Allow private-group admins to promote a member to moderator."""
    group = get_object_or_404(ChatGroup, pk=pk)

    if group.is_public:
        messages.error(request, 'Moderation roles are only used in private groups.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if not _is_group_admin(group, request.user):
        messages.error(request, 'Only group admins can change member roles.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    membership = get_object_or_404(GroupMember, group=group, user_id=user_id)

    if membership.user == group.created_by:
        messages.info(request, 'Group creator already has admin privileges.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if membership.role == GroupMember.ROLE_ADMIN:
        messages.info(request, 'This user is already an admin.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if membership.role == GroupMember.ROLE_MODERATOR:
        messages.info(request, 'This user is already a moderator.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    membership.role = GroupMember.ROLE_MODERATOR
    membership.save(update_fields=['role'])
    messages.success(request, f'{membership.user.get_full_name_display()} is now a moderator.')
    return redirect('professional_chat:chat_group_detail', pk=group.pk)


@login_required
@require_POST
def demote_group_moderator(request, pk, user_id):
    """Allow private-group admins to demote a moderator back to member."""
    group = get_object_or_404(ChatGroup, pk=pk)

    if group.is_public:
        messages.error(request, 'Role management is only available in private groups.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if not _is_group_admin(group, request.user):
        messages.error(request, 'Only group admins can change member roles.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    membership = get_object_or_404(GroupMember, group=group, user_id=user_id)

    if membership.user == group.created_by:
        messages.error(request, 'You cannot change the group creator role.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if membership.role != GroupMember.ROLE_MODERATOR:
        messages.info(request, 'Only moderators can be demoted.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    membership.role = GroupMember.ROLE_MEMBER
    membership.save(update_fields=['role'])
    messages.success(request, f'{membership.user.get_full_name_display()} has been demoted to member.')
    return redirect('professional_chat:chat_group_detail', pk=group.pk)


@login_required
@require_POST
def remove_group_member(request, pk, user_id):
    """Allow private-group admins to remove a member from the group."""
    group = get_object_or_404(ChatGroup, pk=pk)

    if group.is_public:
        messages.error(request, 'Member removal controls are only available in private groups.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if not _is_group_admin(group, request.user):
        messages.error(request, 'Only group admins can remove members.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    membership = get_object_or_404(GroupMember, group=group, user_id=user_id)

    if membership.user == group.created_by:
        messages.error(request, 'You cannot remove the group creator.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    if membership.user == request.user:
        messages.error(request, 'Use the leave button to leave this group yourself.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    removed_name = membership.user.get_full_name_display()
    membership.delete()
    messages.success(request, f'{removed_name} has been removed from the group.')
    return redirect('professional_chat:chat_group_detail', pk=group.pk)


@login_required
@require_POST
def send_message(request, pk):
    """Send a message to a chat group (AJAX endpoint)."""
    group = get_object_or_404(ChatGroup, pk=pk)

    if request.user.is_blocked_for_moderation():
        return JsonResponse(
            {
                'error': 'Your account has been blocked for repeated policy violations.',
                'blocked': True,
                'redirect_url': '/accounts/login/',
            },
            status=403,
        )
    
    # Check if user is member
    if not group.is_member(request.user):
        return JsonResponse({'error': 'Not a member of this group'}, status=403)

    membership = GroupMember.objects.filter(group=group, user=request.user).first()
    if membership is None:
        return JsonResponse({'error': 'Not a member of this group'}, status=403)
    
    content = request.POST.get('content', '').strip()
    attachment = request.FILES.get('attachment')

    if not content and not attachment:
        return JsonResponse({'error': 'Enter a message or attach a file.'}, status=400)

    attachment_error = _validate_chat_attachment(attachment)
    if attachment_error:
        return JsonResponse({'error': attachment_error}, status=400)

    if content:
        moderation = ContentModerator.moderate(content)
        if moderation['is_flagged']:
            violation_state = _handle_violation_attempt(request.user)

            response = {
                'error': 'Message blocked: potential spam, hate speech, or bullying detected.',
                'warning': True,
                'toxicity_reason': moderation['toxicity_reason'],
                'toxicity_score': moderation['toxicity_score'],
                'violations_count': violation_state['violations_count'],
                'violations_remaining': violation_state['violations_remaining'],
                'blocked': violation_state['is_blocked'],
            }

            if violation_state['is_blocked']:
                logout(request)
                response['redirect_url'] = '/accounts/login/'
                response['error'] = 'Your account has been blocked after 10 violations. All your chat messages were removed.'
                return JsonResponse(response, status=403)

            return JsonResponse(response, status=400)
    else:
        moderation = {'toxicity_score': 0.0}

    message = ChatMessage.objects.create(
        group=group,
        sender=request.user,
        content=content,
        attachment=attachment,
        is_flagged=False,
        toxicity_score=moderation['toxicity_score'],
        toxicity_reason='',
    )

    previous_message = (
        ChatMessage.objects
        .filter(group=group, id__lt=message.id, created_at__gte=membership.joined_at)
        .order_by('-id')
        .first()
    )
    while previous_message and _is_system_activity_message(previous_message):
        previous_message = (
            ChatMessage.objects
            .filter(group=group, id__lt=previous_message.id, created_at__gte=membership.joined_at)
            .order_by('-id')
            .first()
        )
    show_sender_name = previous_message is None or previous_message.sender_id != message.sender_id
    show_time_label = show_sender_name

    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'sender_id': message.sender_id,
            'sender': message.get_display_name(),
            'avatar_url': message.get_avatar() or '',
            'show_sender_name': show_sender_name,
            'show_time_label': show_time_label,
            'content': message.content,
            'created_at': _chat_time_label(message.created_at),
            'is_flagged': message.is_flagged,
            'toxicity_reason': message.toxicity_reason,
            'initials': message.get_initials(),
            'attachment_url': message.attachment.url if message.attachment else '',
            'attachment_name': message.get_attachment_name(),
        }
    })


@login_required
def get_messages(request, pk):
    """Return messages created after the given last_id."""
    group = get_object_or_404(ChatGroup, pk=pk)
    if not group.is_member(request.user):
        return JsonResponse({'error': 'Not a member of this group'}, status=403)

    membership = GroupMember.objects.filter(group=group, user=request.user).first()
    if membership is None:
        return JsonResponse({'error': 'Not a member of this group'}, status=403)

    after_id = request.GET.get('after_id')
    messages_qs = group.messages.select_related('sender').filter(created_at__gte=membership.joined_at)
    if after_id and after_id.isdigit():
        messages_qs = messages_qs.filter(id__gt=int(after_id))

    messages_ordered = list(messages_qs.order_by('created_at'))

    previous_sender_id = None
    if after_id and after_id.isdigit():
        previous_message = (
            group.messages
            .filter(id__lte=int(after_id), created_at__gte=membership.joined_at)
            .order_by('-id')
            .first()
        )
        while previous_message and _is_system_activity_message(previous_message):
            previous_message = (
                group.messages
                .filter(id__lt=previous_message.id, created_at__gte=membership.joined_at)
                .order_by('-id')
                .first()
            )
        if previous_message:
            previous_sender_id = previous_message.sender_id

    data = []
    for message in messages_ordered:
        is_system = _is_system_activity_message(message)
        current_time_label = _chat_time_label(message.created_at)
        if is_system:
            show_sender_name = False
            show_time_label = False
        else:
            show_sender_name = message.sender_id != previous_sender_id
            show_time_label = show_sender_name
        data.append(
            {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender': message.get_display_name(),
                'avatar_url': message.get_avatar() or '',
                'is_system': is_system,
                'show_sender_name': show_sender_name,
                'show_time_label': show_time_label,
                'content': message.content,
                'created_at': current_time_label,
                'is_flagged': message.is_flagged,
                'toxicity_reason': message.toxicity_reason,
                'initials': message.get_initials(),
                'attachment_url': message.attachment.url if message.attachment else '',
                'attachment_name': message.get_attachment_name(),
            }
        )
        previous_sender_id = None if is_system else message.sender_id

    return JsonResponse({'success': True, 'messages': data})


@login_required
@require_POST
def edit_group_message(request, pk, message_id):
    """Allow sender to edit own group message content."""
    group = get_object_or_404(ChatGroup, pk=pk)
    message = get_object_or_404(ChatMessage, pk=message_id, group=group, sender=request.user)

    if _is_system_activity_message(message):
        return JsonResponse({'error': 'System activity messages cannot be edited.'}, status=400)

    content = request.POST.get('content', '').strip()
    if not content and not message.attachment:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    message.content = content
    message.save(update_fields=['content'])
    return JsonResponse({'success': True, 'message_id': message.id, 'content': message.content})


@login_required
@require_POST
def delete_group_message(request, pk, message_id):
    """Allow sender to delete own group message."""
    group = get_object_or_404(ChatGroup, pk=pk)
    message = get_object_or_404(ChatMessage, pk=message_id, group=group, sender=request.user)

    if _is_system_activity_message(message):
        return JsonResponse({'error': 'System activity messages cannot be deleted.'}, status=400)

    message.delete()
    return JsonResponse({'success': True, 'deleted': True, 'message_id': message_id})


@login_required
def join_group(request, pk):
    """Join a public chat group."""
    group = get_object_or_404(ChatGroup, pk=pk)
    
    if not group.is_public:
        messages.error(request, 'Cannot join a private group.')
        return redirect('professional_chat:chat_group_list')
    
    if not group.is_member(request.user):
        _add_member_and_announce(group, request.user)
        messages.success(request, f'You have joined {group.name}!')
    else:
        messages.info(request, f'You are already a member of {group.name}.')
    
    return redirect('professional_chat:chat_group_detail', pk=group.pk)


@login_required
def leave_group(request, pk):
    """Leave a chat group."""
    group = get_object_or_404(ChatGroup, pk=pk)
    
    if group.is_member(request.user):
        # Prevent the creator from leaving
        member = GroupMember.objects.get(group=group, user=request.user)
        if member.role == GroupMember.ROLE_ADMIN and group.created_by == request.user:
            messages.error(request, 'Admin cannot leave their own group. Transfer ownership or delete the group.')
        else:
            display_name = request.user.get_full_name_display() or request.user.username
            ChatMessage.objects.create(
                group=group,
                sender=request.user,
                content=f'{display_name} left the group',
                is_flagged=False,
                toxicity_score=0.0,
                toxicity_reason='',
            )
            group.remove_member(request.user)
            messages.success(request, f'You have left {group.name}.')
    
    return redirect('professional_chat:chat_group_list')


@login_required
@require_POST
def delete_chat_group(request, pk):
    """Delete a chat group. Allowed for creator and admins."""
    group = get_object_or_404(ChatGroup, pk=pk)

    if request.user != group.created_by and not request.user.is_admin():
        messages.error(request, 'Only the group creator or an admin can delete this group.')
        return redirect('professional_chat:chat_group_detail', pk=group.pk)

    group_name = group.name
    group.delete()
    messages.success(request, f'Group "{group_name}" was deleted successfully.')
    return redirect('professional_chat:chat_group_list')
