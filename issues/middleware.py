"""
Custom middleware for request/response logging
"""

import json
import time
import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger('issues')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all HTTP requests and responses"""
    
    def process_request(self, request):
        """Called on each request, before Django decides which view to execute"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Called on each response, before returning to the client"""
        # Calculate processing duration
        duration = None
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000  # Convert to milliseconds
        
        # Prepare log data
        log_data = {
            "method": request.method,
            "url": request.get_full_path(),
            "headers": dict(request.headers),
            "body_size": len(request.body) if hasattr(request, 'body') else 0,
            "response_status": response.status_code,
            "response_headers": dict(response.items()),
            "response_size": len(response.content) if hasattr(response, 'content') else 0,
            "duration_ms": round(duration, 2) if duration else None,
            "timestamp": timezone.now().isoformat()
        }
        
        # Include response body for non-successful responses
        if response.status_code >= 400:
            try:
                log_data["response_body"] = response.content.decode('utf-8', errors='ignore')[:1000]
            except:
                log_data["response_body"] = "<unable to decode>"
        
        # Log the request-response pair
        logger.info(json.dumps(log_data))
        
        return response