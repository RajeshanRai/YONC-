from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Event, EventRegistration


def event_list(request):
    now = timezone.now()
    events = Event.objects.all().order_by('start_time')
    context = {
        'events': events,
        'now': now,
        'title': 'Upcoming Events',
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    has_registered = False
    if request.user.is_authenticated:
        has_registered = EventRegistration.objects.filter(event=event, user=request.user).exists()

    # Calculate capacity percentage for progress bar
    capacity_percentage = 0
    if event.is_ticketed and event.total_seats:
        capacity_percentage = int((event.registered_count / event.total_seats) * 100)

    context = {
        'event': event,
        'title': event.title,
        'has_registered': has_registered,
        'capacity_percentage': capacity_percentage,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def register_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if not event.can_register:
        messages.error(request, 'Registration for this event is closed or full.')
        return redirect(event.get_absolute_url())

    registration, created = EventRegistration.objects.get_or_create(event=event, user=request.user)
    if not created:
        messages.info(request, 'You have already registered for this event.')
    else:
        messages.success(request, 'Your registration is confirmed.')

    return redirect(event.get_absolute_url())


@login_required
def unregister_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    registration = EventRegistration.objects.filter(event=event, user=request.user).first()

    if registration:
        registration.delete()
        messages.success(request, 'You have been unregistered from this event.')
    else:
        messages.info(request, 'You are not registered for this event.')

    return redirect(event.get_absolute_url())
