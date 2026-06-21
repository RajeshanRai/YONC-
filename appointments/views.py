from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail

from .models import TimeSlot, Appointment
from .forms import AppointmentForm


@login_required
def book_appointment(request, timeslot_id):
    timeslot = get_object_or_404(TimeSlot.objects.select_related('expert__user'), pk=timeslot_id)
    if not timeslot.is_available:
        messages.error(request, 'This time slot is no longer available.')
        return redirect('expert_detail', pk=timeslot.expert.pk)
    if timeslot.expert.user == request.user:
        messages.error(request, 'You cannot book a consultation with yourself.')
        return redirect('expert_detail', pk=timeslot.expert.pk)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.expert = timeslot.expert
            appointment.timeslot = timeslot
            appointment.status = Appointment.STATUS_CONFIRMED
            appointment.save()
            timeslot.update_booked_status()

            # Send basic confirmation email if email backend is configured.
            if request.user.email and timeslot.expert.user.email:
                subject = f'Appointment confirmed with {timeslot.expert.user.get_full_name_display()}'
                message = (
                    f'Hello {request.user.get_full_name_display()},\n\n'
                    f'Your consultation with {timeslot.expert.user.get_full_name_display()} is confirmed for {timeslot.get_display_window()}.\n\n'
                    f'Appointment topic: {appointment.subject}\n\n'
                    f'Thank you for using YONC.'
                )
                send_mail(subject, message, None, [request.user.email], fail_silently=True)

            messages.success(request, 'Your appointment has been booked successfully.')
            return redirect(appointment.get_absolute_url())
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm()

    context = {
        'timeslot': timeslot,
        'form': form,
        'title': 'Book Consultation',
    }
    return render(request, 'appointments/book_appointment.html', context)


@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(user=request.user).select_related('expert__user', 'timeslot')
    context = {
        'appointments': appointments,
        'title': 'My Appointments',
    }
    return render(request, 'appointments/my_appointments.html', context)


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related('expert__user', 'timeslot'), pk=pk)
    if appointment.user != request.user and appointment.expert.user != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have access to this appointment.')
        return redirect('home')

    context = {
        'appointment': appointment,
        'title': 'Appointment Details',
    }
    return render(request, 'appointments/appointment_detail.html', context)
