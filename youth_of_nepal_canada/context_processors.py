from django.utils import timezone


def current_timezone(request):
    return {
        'current_timezone': timezone.get_current_timezone_name(),
    }
