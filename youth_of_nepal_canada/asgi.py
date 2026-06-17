"""
ASGI config for youth_of_nepal_canada project.
It exposes the ASGI callable as a module-level variable named ``application``.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'youth_of_nepal_canada.settings')

application = get_asgi_application()
