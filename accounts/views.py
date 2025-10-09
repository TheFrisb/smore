import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView, RedirectView, TemplateView
from google.auth.transport import requests
from google.oauth2 import id_token
from honeypot.decorators import check_honeypot

from accounts.forms.login_form import LoginForm
from accounts.forms.register_form import RegisterForm
from accounts.forms.reset_password import PasswordResetRequestForm, SetNewPasswordForm
from accounts.mixins import RedirectAuthenticatedUserMixin
from accounts.models import Referral, User, WithdrawalRequest
from accounts.services.referral_service import ReferralService
from accounts.services.user_service import UserService
from core.models import FrequentlyAskedQuestion
from facebook.services.facebook_pixel import FacebookPixel
from subscriptions.models import UserSubscription

logger = logging.getLogger(__name__)


class BaseAccountView(LoginRequiredMixin):
    login_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        # if email is not verified, add message and continue dispatch as normal
        if request.user.is_authenticated and not request.user.is_email_verified:
            messages.warning(
                request,
                _(
                    "We've sent you an email to verify your account. Please check your inbox."
                ),
                extra_tags="email-verification",
            )

        return super().dispatch(request, *args, **kwargs)


class LoginUserView(RedirectAuthenticatedUserMixin, LoginView):
    template_name = "accounts/pages/login.html"
    form_class = LoginForm

    def get_success_url(self):
        return self.request.GET.get("next", reverse("core:home"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Login")
        return context


class LogoutUserView(LogoutView):
    next_page = "core:home"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Logout")
        return context


@method_decorator(check_honeypot, name="post")
class RegisterUserView(RedirectAuthenticatedUserMixin, TemplateView):
    def __init__(self):
        super().__init__()

    template_name = "accounts/pages/register.html"

    def get(self, request, *args, **kwargs):
        form = RegisterForm()
        return self.render_to_response({"form": form})

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            return self.render_to_response({"form": form})

        user = User.objects.create(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=make_password(form.cleaned_data["password"]),
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
        )

        logger.info(f"[Form Page] User {user.username} created.")

        referral_code = request.session.get("referral_code", None)
        if referral_code:
            if not self._handle_two_level_referral(referral_code, user, form):
                request.session.pop("referral_code", None)
                return self.render_to_response({"form": form})

        authenticated_user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )

        if authenticated_user is not None:
            login(request, authenticated_user)
            request.session.pop("referral_code", None)
            logger.info(f"User {user.username} registered successfully.")

            self.log_request_info(request)

            try:
                fb_pixel = FacebookPixel(request)
                fb_pixel.complete_registration()
            except Exception as e:
                logger.error(
                    "Error sending Complete Registration Facebook Pixel event",
                    exc_info=e,
                )

            return redirect("accounts:my_account")
        else:

            form.add_error(
                None,
                _(
                    "An unexpected error has occured. Please try again or contact support."
                ),
            )

        return self.render_to_response({"form": form})

    def log_request_info(self, request):
        logger.info("Request Headers: %s", dict(request.headers))

        user_agent = request.headers.get("User-Agent", "unknown")
        logger.info("User Agent: %s", user_agent)

        if request.method == "POST":
            logger.info("Request POST Data: %s", dict(request.POST))
        else:
            logger.info("Request GET Data: %s", dict(request.GET))

    def create_user(self, form):
        """
        Create a new user from the form data.
        """
        return User.objects.create(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=make_password(form.cleaned_data["password"]),
            first_name=form.cleaned_data["full_name"].split()[0],
            last_name=form.cleaned_data["full_name"].split()[1],
        )

    def _handle_two_level_referral(self, referral_code: str, user: User, form) -> bool:
        """
        Creates:
          - Referral(referrer=referrer, referred=user, level=1)
          - If referrer also has a parent at level=1, create (grandparent->user, level=2)
        Return True if successful, or False if we added errors to the form.
        """
        # 1) Fetch the referrer user
        referrer = self._get_referrer_by_code(referral_code, form)
        if not referrer:
            form.add_error(
                None,
                _(
                    "An unexpected error has occured. Please try again or contact support."
                ),
            )
            return False

        if referrer == user:
            form.add_error(None, "You cannot refer yourself.")
            return False

        created_direct = self._create_direct_referral(referrer, user, form)
        if not created_direct:
            # The helper or constraints added an error
            return False

        logger.info(f"{user.username} is referred by {referrer.username} (level=1).")

        # 3) Check if referrer also has a direct parent (grandparent)
        #    If so, create a second-level row for the new user
        grandparent = self._get_grandparent_user(referrer)
        if grandparent and grandparent != user:
            created_second = self._create_second_level_referral(grandparent, user, form)
            if not created_second:
                return False
            logger.info(
                f"{user.username} also referred by {grandparent.username} (level=2)."
            )

        return True

    def _get_referrer_by_code(self, referral_code: str, form) -> User | None:
        """
        Return the User who owns this referral code, or None if invalid.
        In case of None, we add an error to the form.
        """
        try:
            return User.objects.get(referral_code=referral_code)
        except User.DoesNotExist:
            form.add_error(None, _("Invalid referral code. Please enter a valid code."))
            logger.error(f"Could not match referral code: {referral_code} to a user.")
            return None

    def _create_direct_referral(self, referrer: User, referred: User, form) -> bool:
        """
        Create the row (referrer->referred, level=1).
        Returns True if created, False if an error occurs.
        """
        from django.db import IntegrityError

        try:
            _, created = Referral.objects.get_or_create(
                referrer=referrer,
                referred=referred,
                defaults={"level": Referral.Level.DIRECT},
            )
        except IntegrityError as e:
            # Possibly a foreign key constraint or duplication
            form.add_error(None, "A database error occurred. Please try again.")
            logger.exception("Error creating direct referral", exc_info=e)
            return False

        if not created:
            # The row already existed, which might be suspicious, but
            # we can just ignore it or treat it as an error. Here we ignore.
            logger.debug("Direct referral row already existed.")
        return True

    def _get_grandparent_user(self, referrer: User) -> User | None:
        """
        Returns the 'grandparent' user if referrer has a level=1 parent,
        or None if none exist.
        """
        # If the referrer was also referred by someone at level=1,
        # that someone is the "grandparent".
        grandparent_ref = Referral.objects.filter(referred=referrer, level=1).first()
        if grandparent_ref:
            return grandparent_ref.referrer
        return None

    def _create_second_level_referral(
        self, grandparent: User, referred: User, form
    ) -> bool:
        """
        Create row (grandparent->referred, level=2).
        Returns True if successful, False if an error was added to the form.
        """
        from django.db import IntegrityError

        try:
            _, created = Referral.objects.get_or_create(
                referrer=grandparent, referred=referred, defaults={"level": 2}
            )
        except IntegrityError as e:
            form.add_error(None, "A database error occurred. Please try again.")
            logger.exception("Error creating second-level referral", exc_info=e)
            return False

        return True

    def login_user(self, request, form):
        """
        Authenticate and log in the user.
        """
        authenticated_user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if authenticated_user is not None:
            login(request, authenticated_user)
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register"
        return context


class MyAccountView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/my_account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["page_title"] = _("My Account")
        return context


class MyNetworkView(BaseAccountView, TemplateView):
    def __init__(self):
        super().__init__()
        self.referral_service = ReferralService()

    template_name = "accounts/pages/my_network.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["network"] = self.referral_service.build_network(self.request.user)
        context["page_title"] = _("My Network")
        return context


class ManagePlanView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/manage_plan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_plans_url"] = self.get_view_plans_url(self.request)
        context["page_title"] = _("Manage Plan")
        context["user_subscriptions"] = self._get_user_subscriptions()
        return context

    def _get_user_subscriptions(self):
        return UserSubscription.objects.filter(
            user=self.request.user, is_active=True
        ).select_related(
            "product_price",
            "product_price__product",
        )

    def get_view_plans_url(self, request):
        return reverse("subscriptions:plans")


class RequestWithdrawalView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/request_withdrawal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Request Withdrawal")
        return context


class ContactUsView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/contact_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Support")
        return context


class FaqView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["faq"] = FrequentlyAskedQuestion.objects.all().order_by("order")
        context["page_title"] = "FAQ"
        return context


class ReferralProgram(BaseAccountView, TemplateView):
    template_name = "accounts/pages/referral_program.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Referral Program")
        return context


class PasswordResetRequestSuccessView(TemplateView):
    template_name = "accounts/password_reset_request_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Password Reset Request")
        return context


class PasswordResetRequestView(FormView):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    template_name = "accounts/request_reset_password.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("accounts:password_reset_request_success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Password Reset Request")
        return context

    def form_valid(self, form):
        """
        If the form is valid, generate a token (if user exists) and send the link.
        We'll show a success message in either case (not revealing existence of user).
        """
        email = form.cleaned_data["email"]
        try:
            user = User.objects.get(email=email, provider=User.ProviderType.INTERNAL)
        except User.DoesNotExist:
            user = None

        if user:
            self.user_service.send_password_change_link(user)

        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = SetNewPasswordForm
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, uidb64, token, *args, **kwargs):
        """
        We override dispatch to decode the user and check the token
        before doing the usual GET/POST.
        """
        self.validlink = False
        self.user = None

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid, provider=User.ProviderType.INTERNAL)
        except (TypeError, ValueError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            self.validlink = True
            self.user = user

        return super().dispatch(request, uidb64, token, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["validlink"] = self.validlink
        return context

    def form_valid(self, form):
        """
        If the token is valid and passwords match,
        set the new password, logout the user, and redirect.
        """
        if not self.validlink or not self.user:
            messages.error(
                self.request, _("Password reset link is invalid or has expired.")
            )
            return redirect("accounts:password_reset")

        new_password = form.cleaned_data["new_password"]
        self.user.set_password(new_password)
        self.user.save()

        # Log out if the user was authenticated
        logout(self.request)

        messages.success(self.request, _("Your password has been reset."))
        return super().form_valid(form)


class WithdrawalHistoryView(BaseAccountView, ListView):
    template_name = "accounts/pages/withdrawal_history.html"
    context_object_name = "withdrawals"

    def get_queryset(self):
        withdrawal_qs = WithdrawalRequest.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

        return withdrawal_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Withdrawal History")
        context["withdrawal_stats"] = self.get_withdrawal_stats()
        context["WithdrawalStatus"] = WithdrawalRequest.Status
        return context

    def get_withdrawal_stats(self):
        qs = self.get_queryset()
        stats = qs.aggregate(
            total_withdrawn_amount=Sum(
                "amount", filter=Q(status=WithdrawalRequest.Status.COMPLETED)
            ),
            total_completed=Count(
                "id", filter=Q(status=WithdrawalRequest.Status.COMPLETED)
            ),
            total_rejected=Count(
                "id", filter=Q(status=WithdrawalRequest.Status.REJECTED)
            ),
            total_in_progress=Count(
                "id",
                filter=Q(
                    status__in=[
                        WithdrawalRequest.Status.PENDING,
                        WithdrawalRequest.Status.PROCESSING,
                        WithdrawalRequest.Status.APPROVED,
                    ]
                ),
            ),
        )

        for key, value in stats.items():
            stats[key] = value or 0

        return stats


class VerifyEmailView(RedirectView):
    """
    Verifies the user’s email by decoding uidb64 and validating the token.
    If valid, the user is activated and redirected to accounts:my_account.
    Otherwise, we redirect to core:home with an error message.
    """

    # We won't hardcode pattern_name because we need logic
    # to decide which URL to return (success vs failure).
    permanent = False  # HTTP status code 302 (temporary) instead of 301

    def get_redirect_url(self, uidb64=None, token=None, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save()
            logger.info(f"User {user.username} email verified.")

            messages.success(
                self.request, _("Your email has been confirmed! Welcome aboard.")
            )

            # log the user in
            login(self.request, user)

            return reverse("accounts:my_account")
        else:
            messages.error(
                self.request, _("Invalid or expired email confirmation link.")
            )
            logger.error("Invalid or expired email confirmation link.")
            return reverse("core:home")


@csrf_exempt
def google_receiver(request):
    """
    Google Call Back
    """
    if request.method != "POST":
        logger.error("Google Receiver called with non-POST request.")
        raise PermissionDenied("Invalid request method.")

    credential = request.POST.get("credential", None)

    if not credential:
        logger.error("Google Receiver called without credential in POST data.")
        raise PermissionDenied("Missing credential in POST data.")

    try:
        user_data = id_token.verify_oauth2_token(
            credential, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )
    except ValueError:
        logger.error("Google Receiver called with invalid credential.")
        raise PermissionDenied("Invalid credential.")

    logger.info(f"Google Receiver data: {user_data}")

    email = user_data.get("email", None)
    sub = user_data.get("sub", None)

    # get or create user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "provider": User.ProviderType.GOOGLE,
            "google_sub": sub,
            "is_email_verified": True,
        },
    )

    if created:
        logger.info(f"User: {user.username} created via Google OAuth.")
    else:
        logger.info(f"User: {user.username} logged in via Google OAuth.")

    login(request, user)

    return redirect("accounts:my_account")
