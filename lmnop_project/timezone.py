from django.utils import timezone
import pytz

class TimezoneDefault:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(pytz.timezone('America/Chicago'))
        return self.get_response(request)