import logging

from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

from accounts.forms.register_form import RegisterForm
from accounts.models import User, Referral
from accounts.services.referral_service import ReferralService
from core.models import FrequentlyAskedQuestion

logger = logging.getLogger(__name__)


class BaseAccountView(LoginRequiredMixin):
    login_url = reverse_lazy("accounts:login")


class LoginUserView(LoginView):
    template_name = "accounts/pages/login.html"

    def get_success_url(self):
        return self.request.GET.get("next", reverse("accounts:my_account"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Login"
        return context


class LogoutUserView(LogoutView):
    next_page = "core:home"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Logout"
        return context


class RegisterUserView(TemplateView):
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
            first_name=form.cleaned_data["full_name"].split()[0],
            last_name=form.cleaned_data["full_name"].split()[1],
        )

        logger.info(f"User {user.username} created.")

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
            return redirect("accounts:my_account")
        else:

            form.add_error(
                None,
                "An unexpected error has occured. Please try again or contact support.",
            )

        return self.render_to_response({"form": form})

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
                "An unexpected error has occured. Please try again or contact support.",
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
            form.add_error(None, "Invalid referral code. Please enter a valid code.")
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
        context["page_title"] = "My Account"
        return context


class MyNetworkView(BaseAccountView, TemplateView):
    def __init__(self):
        super().__init__()
        self.referral_service = ReferralService()

    template_name = "accounts/pages/my_network.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["network"] = self.referral_service.build_network(self.request.user)
        context["page_title"] = "My Network"
        return context


class ManagePlanView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/manage_plan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_plans_url"] = self.get_view_plans_url(self.request)
        context["page_title"] = "Manage Plan"
        return context

    def get_view_plans_url(self, request):
        if request.user.subscription_is_active:
            return reverse("payments:update_subscription")

        return reverse("core:plans")


class RequestWithdrawalView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/request_withdrawal.html"

    def get_success_url(self):
        return reverse("accounts:my_account")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Request Withdrawal"
        return context


class ContactUsView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/contact_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Support"
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
        context["page_title"] = "Referral Program"
        return context
