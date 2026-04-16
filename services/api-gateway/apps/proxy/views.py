"""
API Gateway - Reverse Proxy Views
==================================
Routes incoming requests to the appropriate downstream microservice.

Flow:
  /api/{service_name}/{path} → http://{service}:8000/{service_name}/{path}

Supported methods: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
All headers, query parameters, and body content are forwarded transparently.
"""
import logging
import requests
from django.conf import settings
from django.http import (
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
)
from django.views import View

logger = logging.getLogger(__name__)

# Headers that should NOT be forwarded to downstream services
HOP_BY_HOP_HEADERS = frozenset({
    'connection', 'keep-alive', 'proxy-authenticate',
    'proxy-authorization', 'te', 'trailers',
    'transfer-encoding', 'upgrade', 'host',
    'content-length', 'content-encoding',
})


class HealthCheckView(View):
    """Gateway health check."""

    def get(self, request):
        service_status = {}
        for name, url in settings.SERVICE_ROUTES.items():
            try:
                resp = requests.get(f'{url}/', timeout=3)
                service_status[name] = {
                    'status': 'up' if resp.status_code < 500 else 'down',
                    'code': resp.status_code,
                }
            except requests.RequestException:
                service_status[name] = {'status': 'down', 'code': 0}

        all_up = all(s['status'] == 'up' for s in service_status.values())
        return JsonResponse({
            'status': 'healthy' if all_up else 'degraded',
            'service': 'api-gateway',
            'services': service_status,
        }, status=200 if all_up else 503)


class ServiceRegistryView(View):
    """List all registered services and their base URLs."""

    def get(self, request):
        services = []
        for name, url in settings.SERVICE_ROUTES.items():
            services.append({
                'name': name,
                'prefix': f'/api/{name}/',
                'upstream': url,
            })
        return JsonResponse({
            'gateway': 'Django API Gateway',
            'services': services,
        })


class ServiceProxyView(View):
    """
    Generic reverse proxy view.
    Captures the service name and remaining path from the URL,
    then proxies the request to the matching microservice.
    """

    def dispatch(self, request, service_name, path=''):
        """Route any HTTP method to the proxy handler."""
        service_url = settings.SERVICE_ROUTES.get(service_name)

        if service_url is None:
            logger.warning(f'Unknown service requested: {service_name}')
            return JsonResponse(
                {'error': f'Service "{service_name}" not found'},
                status=404,
            )

        return self._proxy_request(request, service_name, service_url, path)

    def _proxy_request(self, request, service_name, service_url, path):
        """Forward the request to the downstream service and return its response."""
        # Build the upstream URL: service_url/{service_name}/{path}?{query}
        upstream_path = f'/{service_name}/{path}' if path else f'/{service_name}/'
        upstream_url = f'{service_url}{upstream_path}'

        if request.META.get('QUERY_STRING'):
            upstream_url += f'?{request.META["QUERY_STRING"]}'

        method = request.method.lower()

        # Build headers to forward
        headers = self._build_headers(request)

        # Get request body
        body = request.body if request.body else None

        logger.info(
            f'[PROXY] {request.method} /api/{service_name}/{path} '
            f'→ {upstream_url}'
        )

        try:
            response = requests.request(
                method=method,
                url=upstream_url,
                headers=headers,
                data=body,
                timeout=settings.PROXY_TIMEOUT,
                allow_redirects=False,
                stream=True,
            )
        except requests.ConnectionError:
            logger.error(f'Service {service_name} is unreachable at {service_url}')
            return JsonResponse(
                {
                    'error': 'Service unavailable',
                    'service': service_name,
                    'detail': f'Cannot connect to {service_name}',
                },
                status=502,
            )
        except requests.Timeout:
            logger.error(f'Service {service_name} timed out')
            return JsonResponse(
                {
                    'error': 'Service timeout',
                    'service': service_name,
                    'detail': f'{service_name} did not respond within {settings.PROXY_TIMEOUT}s',
                },
                status=504,
            )
        except requests.RequestException as e:
            logger.error(f'Proxy error for {service_name}: {e}')
            return JsonResponse(
                {'error': 'Gateway error', 'detail': str(e)},
                status=502,
            )

        # Build Django response from upstream response
        django_response = self._build_response(response)

        logger.info(
            f'[PROXY] {request.method} /api/{service_name}/{path} '
            f'← {response.status_code}'
        )

        return django_response

    def _build_headers(self, request):
        """Extract and forward relevant headers from the incoming request."""
        headers = {}
        for key, value in request.META.items():
            # Django stores HTTP headers as HTTP_X_xxx in META
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').lower()
                if header_name not in HOP_BY_HOP_HEADERS:
                    headers[header_name] = value
            elif key == 'CONTENT_TYPE' and value:
                headers['content-type'] = value

        # Forward the real client IP
        client_ip = request.META.get('REMOTE_ADDR', '')
        existing_forwarded = headers.get('x-forwarded-for', '')
        if existing_forwarded:
            headers['x-forwarded-for'] = f'{existing_forwarded}, {client_ip}'
        else:
            headers['x-forwarded-for'] = client_ip

        headers['x-forwarded-host'] = request.get_host()
        headers['x-forwarded-proto'] = request.scheme

        return headers

    def _build_response(self, upstream_response):
        """Convert an upstream requests.Response into a Django HttpResponse."""
        content = upstream_response.content

        django_response = HttpResponse(
            content=content,
            status=upstream_response.status_code,
        )

        # Forward response headers
        for key, value in upstream_response.headers.items():
            header_lower = key.lower()
            if header_lower not in HOP_BY_HOP_HEADERS:
                django_response[key] = value

        return django_response


class FrontendProxyView(View):
    """
    Proxy non-API requests to the frontend dev server.
    Handles all non-API routes so the SPA works correctly.
    """

    def dispatch(self, request, path=''):
        frontend_url = settings.FRONTEND_URL
        upstream_url = f'{frontend_url}/{path}'

        if request.META.get('QUERY_STRING'):
            upstream_url += f'?{request.META["QUERY_STRING"]}'

        method = request.method.lower()
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').lower()
                if header_name not in HOP_BY_HOP_HEADERS:
                    headers[header_name] = value

        # Preserve the original Host header so Vite's allowedHosts check passes.
        # Without this, Vite sees the internal Docker hostname 'frontend'
        # and blocks the request.
        headers['host'] = request.get_host()

        body = request.body if request.body else None

        try:
            response = requests.request(
                method=method,
                url=upstream_url,
                headers=headers,
                data=body,
                timeout=30,
                allow_redirects=False,
                stream=True,
            )
        except requests.RequestException:
            return JsonResponse(
                {'error': 'Frontend service unavailable'},
                status=502,
            )

        django_response = HttpResponse(
            content=response.content,
            status=response.status_code,
        )
        for key, value in response.headers.items():
            header_lower = key.lower()
            if header_lower not in HOP_BY_HOP_HEADERS:
                django_response[key] = value

        return django_response
