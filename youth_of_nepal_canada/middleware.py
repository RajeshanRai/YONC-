from django.utils import timezone
from zoneinfo import ZoneInfo
from urllib.parse import unquote


class DeviceTimezoneMiddleware:
    """Activate timezone based on browser-provided cookie if valid."""

    COOKIE_KEY = 'user_tz'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_name = request.COOKIES.get(self.COOKIE_KEY)

        if tz_name:
            tz_name = unquote(tz_name)
            try:
                timezone.activate(ZoneInfo(tz_name))
            except Exception:
                timezone.deactivate()
        else:
            timezone.deactivate()

        response = self.get_response(request)
        return response
