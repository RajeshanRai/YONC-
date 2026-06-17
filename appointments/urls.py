from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('book/<int:timeslot_id>/', views.book_appointment, name='book_appointment'),
    path('my/', views.my_appointments, name='my_appointments'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
]
