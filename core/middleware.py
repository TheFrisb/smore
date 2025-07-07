from django.shortcuts import redirect


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
