from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token


class CustomCSRFMiddleware(MiddlewareMixin):
    """Custom CSRF middleware to handle token refresh and validation"""
    
    def process_request(self, request):
        """Process request and ensure CSRF token is available"""
        # Ensure CSRF token is available for all requests
        if request.method == 'GET':
            get_token(request)
        return None
