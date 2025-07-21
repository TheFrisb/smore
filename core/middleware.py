import logging

from django.contrib.gis.geoip2 import GeoIP2
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Simply pass the request to the next middleware or view
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if the URL has been resolved
        if request.resolver_match and request.user.is_authenticated:
            app_name = request.resolver_match.app_name
            url_name = request.resolver_match.url_name

            # Apply logic only to 'core' and 'accounts' apps, excluding specified paths
            if (app_name == 'core' and url_name != 'verify_email') or \
                    (app_name == 'accounts' and url_name not in ['verify_email', 'google_receiver',
                                                                 'password_reset_confirm', 'password_reset', 'logout']):
                # Redirect if user is authenticated but email is not verified
                if request.user.is_authenticated and not request.user.is_email_verified:
                    return redirect('core:verify_email')

        return None  # Continue processing the request if no redirection occurs


class GeoIpSwitzerlandDetector(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.log = logging.getLogger(self.__class__.__name__)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(request, 'is_switzerland'):
            ip_addr = self._get_client_ip(request)
            g = GeoIP2()
            try:
                country = g.country(ip_addr)
                request.is_switzerland = (country['country_code'] == 'CH')
                self.log.info(f"GeoIP lookup for IP {ip_addr}: {country['country_name']} ({country['country_code']})")
            except Exception as e:
                self.log.error(f"GeoIP lookup failed for IP {ip_addr}: {e}")
                request.is_switzerland = False

        return None
