from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import ContactForm


@require_http_methods(["GET", "POST"])
def contact_us(request):
    """Handle contact form submission and display contact page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            messages.success(
                request,
                'Thank you for your message! We\'ll get back to you soon.',
                extra_tags='contact_success'
            )
            return redirect('contact_us')
    else:
        form = ContactForm()

    context = {
        'form': form,
    }
    return render(request, 'contact/contact_us.html', context)
