from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from accounts.models import User
from experts.models import ExpertProfile
from .models import Message, Conversation


@login_required
def inbox(request):
    """Display user's message inbox with conversations."""
    user = request.user
    
    # Get all conversations
    conversations = Conversation.objects.filter(
        Q(participant1=user) | Q(participant2=user)
    ).select_related('participant1', 'participant2', 'last_message')
    
    # Build conversation data
    conversation_list = []
    for conv in conversations:
        other = conv.get_other_participant(user)
        unread = conv.get_unread_count(user)
        
        conversation_list.append({
            'conversation': conv,
            'other_user': other,
            'unread_count': unread,
            'last_message': conv.last_message,
        })
    
    # Sort by last message timestamp
    conversation_list.sort(key=lambda x: x['conversation'].updated_at, reverse=True)
    
    # Total unread
    total_unread = Message.objects.filter(receiver=user, is_read=False).count()
    
    context = {
        'conversations': conversation_list,
        'total_unread': total_unread,
        'title': 'Messages',
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def chat_view(request, user_id):
    """Display chat interface with a specific user."""
    user = request.user
    other_user = get_object_or_404(User, id=user_id, is_active=True)
    
    if other_user.id == user.id:
        messages.error(request, 'You cannot chat with yourself.')
        return redirect('inbox')
    
    # Get or create conversation
    conversation = Conversation.get_or_create_conversation(user, other_user)
    
    # Get messages between these two users
    messages_qs = Message.objects.filter(
        (Q(sender=user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=user))
    ).select_related('sender', 'receiver').order_by('timestamp')
    
    # Mark unread messages as read
    unread_messages = Message.objects.filter(
        sender=other_user,
        receiver=user,
        is_read=False
    )
    unread_count = unread_messages.count()
    unread_messages.update(is_read=True)
    
    # Paginate messages (show last 50, load more on scroll)
    paginator = Paginator(messages_qs, 50)
    page_obj = paginator.get_page(paginator.num_pages)  # Get last page
    
    # Check if other user is an expert
    expert_profile = ExpertProfile.objects.filter(user=other_user, is_approved=True).first()
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': page_obj,
        'expert_profile': expert_profile,
        'unread_count': unread_count,
        'title': f'Chat with {other_user.get_full_name_display()}',
    }
    return render(request, 'messaging/chat.html', context)


@login_required
@require_POST
def send_message(request):
    """AJAX endpoint to send a message."""
    receiver_id = request.POST.get('receiver_id')
    content = request.POST.get('content', '').strip()
    
    if not receiver_id or not content:
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)
    
    try:
        receiver = User.objects.get(id=receiver_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    
    if receiver.id == request.user.id:
        return JsonResponse({'status': 'error', 'message': 'Cannot message yourself'}, status=400)
    
    # Create message
    message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content
    )
    
    # Update conversation
    conversation = Conversation.get_or_create_conversation(request.user, receiver)
    conversation.last_message = message
    conversation.save()
    
    return JsonResponse({
        'status': 'success',
        'message_id': message.id,
        'timestamp': message.get_timestamp_display(),
        'content': message.content,
    })


@login_required
def get_messages(request, user_id):
    """AJAX endpoint to get new messages."""
    other_user = get_object_or_404(User, id=user_id)
    last_id = request.GET.get('last_id', 0)
    
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0
    
    # Get new messages from other user
    new_messages = Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        id__gt=last_id
    ).select_related('sender').order_by('timestamp')
    
    # Mark as read
    new_messages.filter(is_read=False).update(is_read=True)
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.get_timestamp_display(),
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.get_full_name_display(),
        })
    
    return JsonResponse({
        'status': 'success',
        'messages': messages_data,
        'count': len(messages_data),
    })


@login_required
def get_conversations(request):
    """AJAX endpoint to get conversation list with unread counts."""
    user = request.user
    
    conversations = Conversation.objects.filter(
        Q(participant1=user) | Q(participant2=user)
    ).select_related('participant1', 'participant2', 'last_message')[:20]
    
    data = []
    for conv in conversations:
        other = conv.get_other_participant(user)
        unread = conv.get_unread_count(user)
        
        data.append({
            'user_id': other.id,
            'name': other.get_full_name_display(),
            'avatar': other.get_profile_picture_url(),
            'unread': unread,
            'last_message': conv.last_message.content[:50] if conv.last_message else '',
            'last_timestamp': conv.last_message.get_timestamp_display() if conv.last_message else '',
        })
    
    total_unread = Message.objects.filter(receiver=user, is_read=False).count()
    
    return JsonResponse({
        'status': 'success',
        'conversations': data,
        'total_unread': total_unread,
    })


@login_required
def start_chat(request, expert_id):
    """Start a chat with an expert."""
    expert = get_object_or_404(ExpertProfile, id=expert_id, is_approved=True)
    return redirect('chat_view', user_id=expert.user.id)
