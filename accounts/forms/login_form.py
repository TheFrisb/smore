import logging

from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q

from accounts.models import User

logger = logging.getLogger(__name__)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if not username or not password:
            return self.cleaned_data

        print(f"username: {username}, password: {password}")

        try:
            user = User.objects.get(
                Q(username=username)
                | Q(email__iexact=username, provider=User.ProviderType.INTERNAL)
            )
            logger.info(f"Found user with username: {username}")
        except User.DoesNotExist:
            logger.info(f"Failed to find user with username: {username}")
            raise self.get_invalid_login_error()
        except User.MultipleObjectsReturned:
            logger.error(f"Multiple users found with username: {username}")
            raise self.get_invalid_login_error()

        self.user_cache = authenticate(username=user.username, password=password)

        if self.user_cache is None:
            logger.info(f"Failed login with username: {username}")
            raise self.get_invalid_login_error()

        self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
