"""
Custom middleware for request logging and audit trail.
Logs all authenticated requests to the database for security and compliance.
"""
from django.utils.deprecation import MiddlewareMixin
from core.models import AuditLog
from core.utils import get_client_ip


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs authenticated user requests to the database.
    
    Records:
    - User identifier
    - Endpoint path
    - HTTP method
    - Timestamp
    - IP address
    - User agent
    - Response status code
    
    Only logs requests from authenticated users to reduce database load.
    Skips static and media file requests.
    """
    
    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/jsi18n/',
    ]
    
    # Methods to exclude from logging (typically GET for static resources)
    EXCLUDED_METHODS = []

    def should_log_request(self, request):
        """
        Determine if request should be logged.
        
        Args:
            request: Django request object
            
        Returns:
            True if request should be logged, False otherwise
        """
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return False
        
        # Skip excluded paths
        for excluded_path in self.EXCLUDED_PATHS:
            if request.path.startswith(excluded_path):
                return False
        
        # Skip excluded methods
        if request.method in self.EXCLUDED_METHODS:
            return False
        
        return True

    def process_request(self, request):
        """
        Process incoming request.
        Store request data for later logging.
        
        Args:
            request: Django request object
        """
        # Store request start time for performance monitoring
        import time
        request._request_start_time = time.time()
        
        return None

    def process_response(self, request, response):
        """
        Process response and log the request.
        
        Args:
            request: Django request object
            response: Django response object
            
        Returns:
            Response object (unchanged)
        """
        # Check if request should be logged
        if not self.should_log_request(request):
            return response
        
        try:
            # Extract request information
            user = request.user if request.user.is_authenticated else None
            endpoint = request.path
            method = request.method
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
            status_code = response.status_code
            
            # Create audit log entry
            AuditLog.objects.create(
                user=user,
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=status_code
            )
        
        except Exception as e:
            # Log error but don't break the request/response cycle
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error logging request: {str(e)}")
        
        return response

    def process_exception(self, request, exception):
        """
        Process exceptions and log them.
        
        Args:
            request: Django request object
            exception: Exception that occurred
            
        Returns:
            None (allows exception to propagate)
        """
        # Check if request should be logged
        if not self.should_log_request(request):
            return None
        
        try:
            # Log the failed request
            user = request.user if request.user.is_authenticated else None
            endpoint = request.path
            method = request.method
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            AuditLog.objects.create(
                user=user,
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=500  # Internal server error
            )
        
        except Exception as e:
            # Log error but don't break exception handling
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error logging exception: {str(e)}")
        
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    
    Adds headers for:
    - XSS protection
    - Content type sniffing prevention
    - Clickjacking protection
    """
    
    def process_response(self, request, response):
        """
        Add security headers to response.
        
        Args:
            request: Django request object
            response: Django response object
            
        Returns:
            Response with added security headers
        """
        # Prevent XSS attacks
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking (already handled by Django's XFrameOptionsMiddleware)
        # response['X-Frame-Options'] = 'DENY'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
