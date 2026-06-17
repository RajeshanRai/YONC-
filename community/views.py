from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError

from .models import ForumPost, ForumComment
from django.http import HttpResponse, Http404, JsonResponse
from django.db.utils import OperationalError
from django.db.models import Prefetch
from services.models import ServiceCategory
from .forms import ForumPostForm, ForumCommentForm
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.safestring import mark_safe

# optional: import helper to convert markdown-style links
try:
    from .templatetags.markdown_extras import markdown_links
except Exception:
    markdown_links = lambda v: v


def forum_home(request):
    categories = ServiceCategory.objects.filter(is_active=True)
    recent_posts = ForumPost.objects.filter(is_active=True).select_related('author', 'category')[:12]
    context = {
        'categories': categories,
        'recent_posts': recent_posts,
        'title': 'Community Forum',
    }
    return render(request, 'community/forum_home.html', context)


def category_detail(request, slug):
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    posts = category.forum_posts.filter(is_active=True).select_related('author')
    context = {
        'category': category,
        'posts': posts,
        'title': category.name,
    }
    return render(request, 'community/category_detail.html', context)


def post_detail(request, pk):
    post = get_object_or_404(ForumPost.objects.select_related('author', 'category'), pk=pk, is_active=True)

    active_replies_prefetch = Prefetch(
        'replies',
        queryset=ForumComment.objects.filter(is_active=True).select_related('author'),
        to_attr='active_replies'
    )
    base_comments_qs = post.comments.filter(is_active=True, parent__isnull=True).select_related('author').prefetch_related(active_replies_prefetch)
    pinned_qs = base_comments_qs.filter(is_pinned=True)
    other_qs = base_comments_qs.filter(is_pinned=False)
    comments = list(pinned_qs) + list(other_qs)

    form = ForumCommentForm() if request.user.is_authenticated else None

    if request.user.is_authenticated and request.method == 'POST':
        form = ForumCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = post.comments.get(pk=parent_id)
                except ForumComment.DoesNotExist:
                    parent_comment = None
                comment.parent = parent_comment
            comment.save()
            messages.success(request, 'Your reply has been posted.')
            return redirect('community:post_detail', pk=post.pk)

    # render markdown-style [text](url) into anchors for post content
    try:
        content_html = markdown_links(post.content or '')
        # preserve manual line breaks
        content_html = content_html.replace('\n', '<br>')
        content_html = mark_safe(content_html)
    except Exception:
        content_html = post.content or ''

    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'title': post.title,
        'post_content_html': content_html,
    }
    # Likes table may not exist yet (migration pending). compute safely.
    try:
        context['likes_count'] = post.likes.count()
    except OperationalError:
        context['likes_count'] = 0
    # whether the current user has liked this post
    try:
        if request.user.is_authenticated:
            context['user_liked'] = post.likes.filter(pk=request.user.pk).exists()
        else:
            context['user_liked'] = False
    except OperationalError:
        context['user_liked'] = False
    return render(request, 'community/post_detail.html', context)


def comment_replies(request, comment_id):
    # Return rendered HTML for direct replies to a comment (AJAX)
    try:
        parent = ForumComment.objects.select_related('post').get(pk=comment_id)
    except ForumComment.DoesNotExist:
        raise Http404()

    # Server-side paginate direct replies
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 10))

    replies_qs = ForumComment.objects.filter(parent=parent, is_active=True).select_related('author')
    paginator = Paginator(replies_qs, page_size)
    try:
        replies_page = paginator.page(page)
    except PageNotAnInteger:
        replies_page = paginator.page(1)
    except EmptyPage:
        replies_page = paginator.page(paginator.num_pages)

    # For each reply, prefetch its immediate active replies (one level) to support nested display
    child_ids = [r.id for r in replies_page.object_list]
    child_replies = ForumComment.objects.filter(parent_id__in=child_ids, is_active=True).select_related('author')
    # Attach active_replies to each parent reply
    children_map = {}
    for cr in child_replies:
        children_map.setdefault(cr.parent_id, []).append(cr)
    for r in replies_page.object_list:
        setattr(r, 'active_replies', children_map.get(r.id, []))

    context = {
        'replies': replies_page.object_list,
        'has_next': replies_page.has_next(),
        'next_page_number': replies_page.next_page_number() if replies_page.has_next() else None,
    }
    html = render_to_string('community/_replies_list.html', context, request=request)
    return HttpResponse(html)


@login_required
def comment_edit(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        comment = ForumComment.objects.select_related('post').get(pk=comment_id, is_active=True)
    except ForumComment.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    if request.user != comment.author:
        return JsonResponse({'error': 'forbidden'}, status=403)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'content required'}, status=400)
    comment.content = content
    comment.save()
    html = render_to_string('community/_comment.html', {'comment': comment}, request=request)
    return JsonResponse({'success': True, 'html': html, 'comment_id': comment.id})


@login_required
def comment_delete(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        comment = ForumComment.objects.select_related('post').get(pk=comment_id, is_active=True)
    except ForumComment.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    # allow author or post owner to delete
    if not (request.user == comment.author or request.user == comment.post.author):
        return JsonResponse({'error': 'forbidden'}, status=403)
    comment.is_active = False
    comment.save()
    return JsonResponse({'success': True, 'comment_id': comment_id})


@login_required
def comment_pin(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        comment = ForumComment.objects.select_related('post').get(pk=comment_id, is_active=True)
    except ForumComment.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    post = comment.post
    if request.user != post.author:
        return JsonResponse({'error': 'forbidden'}, status=403)
    pin = request.POST.get('pin') in ['1', 'true', 'True']
    if pin:
        # unpin others for this post
        ForumComment.objects.filter(post=post, is_pinned=True).update(is_pinned=False)
        comment.is_pinned = True
    else:
        comment.is_pinned = False
    comment.save()
    return JsonResponse({'success': True, 'pinned': comment.is_pinned, 'comment_id': comment.id})


@login_required
def post_like(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    post = get_object_or_404(ForumPost, pk=pk, is_active=True)
    user = request.user
    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})


@login_required
def comment_ajax(request, pk):
    # AJAX endpoint to create a comment (top-level or reply)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if not (request.user.is_expert() or request.user.is_admin()):
        return JsonResponse({'error': 'Only experts and administrators can reply to forum posts.'}, status=403)
    post = get_object_or_404(ForumPost, pk=pk, is_active=True)
    form = ForumCommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    parent_id = request.POST.get('parent_id')
    if parent_id:
        try:
            parent = post.comments.get(pk=parent_id)
        except ForumComment.DoesNotExist:
            parent = None
        comment.parent = parent
    comment.save()

    # Render the single comment HTML and return
    html = render_to_string('community/_comment.html', {'comment': comment}, request=request)
    return JsonResponse({'success': True, 'html': html, 'parent_id': parent_id})


@login_required
def new_post(request):
    if not (request.user.is_expert() or request.user.is_admin()):
        messages.error(request, 'Only experts and administrators can create forum posts.')
        return redirect('community:forum_home')

    if request.method == 'POST':
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            try:
                post.save()
            except IntegrityError:
                messages.error(request, 'There was an error saving your post. The selected category may no longer exist.')
                context = {
                    'form': form,
                    'title': 'New Forum Post',
                    'category_count': ServiceCategory.objects.filter(is_active=True).count(),
                }
                return render(request, 'community/new_post.html', context)

            messages.success(request, 'Your post has been created.')
            return redirect('community:post_detail', pk=post.pk)
    else:
        form = ForumPostForm()

    context = {
        'form': form,
        'title': 'New Forum Post',
        'category_count': ServiceCategory.objects.filter(is_active=True).count(),
    }
    return render(request, 'community/new_post.html', context)


@login_required
def post_edit(request, pk):
    post = get_object_or_404(ForumPost, pk=pk, is_active=True)
    if request.user != post.author:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('community:post_detail', pk=post.pk)

    if request.method == 'POST':
        form = ForumPostForm(request.POST, instance=post)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Post updated successfully.')
                return redirect('community:post_detail', pk=post.pk)
            except IntegrityError:
                messages.error(request, 'There was an error updating the post. Please try again.')
    else:
        form = ForumPostForm(instance=post)

    context = {
        'form': form,
        'title': 'Edit Forum Post',
        'category_count': ServiceCategory.objects.filter(is_active=True).count(),
        'post': post,
    }
    return render(request, 'community/edit_post.html', context)


@login_required
def post_delete(request, pk):
    post = get_object_or_404(ForumPost, pk=pk, is_active=True)
    if request.user != post.author:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('community:post_detail', pk=post.pk)

    if request.method == 'POST':
        # soft-delete
        post.is_active = False
        post.save()
        messages.success(request, 'Post deleted.')
        return redirect('community:forum_home')

    context = {
        'post': post,
        'title': 'Delete Forum Post',
    }
    return render(request, 'community/post_confirm_delete.html', context)
