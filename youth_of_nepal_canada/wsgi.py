"""
WSGI config for youth_of_nepal_canada project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'youth_of_nepal_canada.settings')

application = get_wsgi_application()
