from django.urls import path

from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.tools_home, name='tools_home'),
    path('resume-cover-letter/', views.resume_cover_letter_generator, name='resume_cover_letter_generator'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('resume-cover-letter/export/', views.export_generated_document, name='export_generated_document'),
]
