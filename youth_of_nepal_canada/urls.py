"""
Main URL configuration for youth_of_nepal_canada project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about/', include('about.urls')),
    path('contact/', include('contact.urls')),
    path('', include('accounts.urls')),
    path('services/', include('services.urls')),
    path('experts/', include('experts.urls')),
    path('appointments/', include('appointments.urls')),
    path('events/', include('events.urls')),
    path('community/', include('community.urls')),
    path('messages/', include('messaging.urls')),
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
