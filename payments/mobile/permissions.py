from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from backend import settings


class RevenuecatTokenPermission(BasePermission):
    def has_permission(self, request, view):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('Invalid token header. No credentials provided.')

        token = auth_header.split(' ')[1]

        if token != settings.REVENUECAT_TOKEN:
            raise AuthenticationFailed('Invalid token.')

        return True
