import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import CustomUser


class JWTAuthentication(authentication.BaseAuthentication):
    """Custom JWT authentication for DRF."""

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            user = CustomUser.objects.get(id=payload['user_id'])
            return (user, token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token.')
        except CustomUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found.')
