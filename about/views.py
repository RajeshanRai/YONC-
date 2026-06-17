from django.shortcuts import render
from .models import Partner


def about_view(request):
    """Dynamic About page with mission, history, partners, and contact info."""
    partners = Partner.objects.filter(is_active=True).order_by('sort_order', 'name')
    return render(request, 'about/about.html', {
        'title': 'About Us',
        'partners': partners,
    })
