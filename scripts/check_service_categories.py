import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'youth_of_nepal_canada.settings')
import django
django.setup()
from services.models import ServiceCategory

print('ServiceCategory count:', ServiceCategory.objects.count())
print('IDs:', list(ServiceCategory.objects.values_list('id', flat=True))[:200])
print('Exists id=14:', ServiceCategory.objects.filter(pk=14).exists())
