from django.shortcuts import render, get_object_or_404
from .models import ServiceCategory


def category_list(request):
    """List all active service categories in ascending order."""
    categories = ServiceCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    return render(request, 'services/category_list.html', {
        'categories': categories,
        'title': 'Our Services'
    })


def category_detail(request, slug):
    """Show details of a specific category."""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    experts = category.expert_profiles.filter(is_approved=True).select_related('user')
    return render(request, 'services/category_detail.html', {
        'category': category,
        'experts': experts,
        'title': category.name
    })
