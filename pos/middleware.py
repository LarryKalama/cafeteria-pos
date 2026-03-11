# pos/middleware.py
# Middleware to redirect to first-time setup if no superuser exists

from django.shortcuts import redirect
from django.contrib.auth import get_user_model

class FirstTimeSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        User = get_user_model()

        # Skip the check for these paths to avoid redirect loops or broken assets
        skip_paths = [
            '/setup/',
            '/accounts/login/',
            '/accounts/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]

        # If the request path starts with any skip path → proceed normally
        if any(request.path.startswith(p) for p in skip_paths):
            return self.get_response(request)

        # If no superuser exists in the database → redirect to setup
        if not User.objects.filter(is_superuser=True).exists():
            return redirect('setup')

        # Normal request flow (everything else)
        return self.get_response(request)