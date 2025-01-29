from django.shortcuts import redirect
from django.urls import reverse


class RedirectAuthenticatedUserMixin:
    """
    A mixin that automatically redirects authenticated users
    to a configured URL (default: 'accounts:my_account') before
    processing the request in dispatch().
    """

    # You can override this in your subclass to customize the redirect URL
    redirect_authenticated_url = "accounts:my_account"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_authenticated_redirect_url())
        return super().dispatch(request, *args, **kwargs)

    def get_authenticated_redirect_url(self):
        """
        Returns the URL to redirect to if the user is already authenticated.
        Subclasses can override this method or just override
        `redirect_authenticated_url`.
        """
        return reverse(self.redirect_authenticated_url)
