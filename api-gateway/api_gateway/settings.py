import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-api-gateway-dev-key')
DEBUG = int(os.environ.get('DEBUG', 0))
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'corsheaders',
    'rest_framework',
    'apps.proxy',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'apps.proxy.middleware.RequestLoggingMiddleware',
    'apps.proxy.middleware.GatewayHeadersMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'api_gateway.urls'

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# No database needed for the gateway
DATABASES = {}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
}

# ──────────────────────────────────────────────
# Microservice routing table
# ──────────────────────────────────────────────
SERVICE_ROUTES = {
    'users':    os.environ.get('USER_SERVICE_URL',    'http://user-service:8000'),
    'products': os.environ.get('PRODUCT_SERVICE_URL', 'http://product-service:8000'),
    'cart':     os.environ.get('CART_SERVICE_URL',     'http://cart-service:8000'),
    'orders':   os.environ.get('ORDER_SERVICE_URL',   'http://order-service:8000'),
    'payments': os.environ.get('PAYMENT_SERVICE_URL', 'http://payment-service:8000'),
    'ai':       os.environ.get('AI_SERVICE_URL',      'http://ai-service:8000'),
}

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://frontend:5173')

# Proxy request timeout (seconds)
PROXY_TIMEOUT = int(os.environ.get('PROXY_TIMEOUT', '60'))

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'gateway': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'gateway',
        },
    },
    'loggers': {
        'apps.proxy': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
