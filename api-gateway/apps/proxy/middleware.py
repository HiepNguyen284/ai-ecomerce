"""
API Gateway Middleware
======================
Custom middleware for request/response processing at the gateway level.
"""
import time
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Logs every incoming request with method, path, status code, and duration.
    Provides centralized access logging for all proxied traffic.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f'{request.method} {request.get_full_path()} '
            f'→ {response.status_code} ({duration_ms:.0f}ms)'
        )

        return response


class GatewayHeadersMiddleware:
    """
    Adds gateway identification headers to all responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Gateway'] = 'Django-API-Gateway'
        response['X-Gateway-Version'] = '1.0'
        return response
