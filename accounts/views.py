import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, FormView

from accounts.forms.register_form import RegisterForm
from accounts.forms.withdrawal_request_form import WithdrawalRequestForm
from accounts.models import User, Referral, WithdrawalRequest
from payments.services.internal_stripe_service import InternalStripeService

logger = logging.getLogger(__name__)


class BaseAccountView(LoginRequiredMixin):
    login_url = reverse_lazy("accounts:login")


class LoginUserView(LoginView):
    template_name = "accounts/pages/login.html"
    page_title = "Login"

    def get_success_url(self):
        return self.request.GET.get("next", reverse("accounts:my_account"))


class LogoutUserView(LogoutView):
    next_page = "core:home"
    page_title = "Logout"


class RegisterUserView(TemplateView):
    def __init__(self):
        super().__init__()
        self.stripe_service = InternalStripeService()

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
            try:
                referrer = User.objects.get(referral_code=referral_code)
                Referral.objects.create(referrer=referrer, referred=user)
                logger.info(
                    f"User {user.username} referred by {referrer.username}, through referral code {referral_code}."
                )
            except User.DoesNotExist:
                logger.error(
                    f"Could not match referral code: {referral_code} to an user."
                )
                form.add_error(
                    None, "Invalid referral code. Please enter a valid referral code."
                )
                return self.render_to_response({"form": form})

        self.stripe_service.create_stripe_customer(user)

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

    def handle_referral(self, form, user):
        """
        Handle referral logic if a referral code is provided.
        """
        referral_code = form.cleaned_data.get("referral_code", None)
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                Referral.objects.create(referrer=referrer, referred=user)
            except User.DoesNotExist:
                form.add_error(
                    None, "Invalid referral code. Please enter a valid referral code."
                )
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


class MyAccountView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/my_account.html"


class MyNetworkView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/my_network.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["network"] = self.get_referrals(self.request.user)
        return context

    def get_referrals(self, user):
        first_level_referrals = Referral.objects.filter(referrer=user).select_related(
            "referred"
        )

        second_level_referrals = Referral.objects.filter(
            referrer__in=[referral.referred for referral in first_level_referrals]
        ).select_related("referrer", "referred")

        network = {
            "first_level": [
                {
                    "user": referral.referred,
                    "second_level": [
                        second.referred
                        for second in second_level_referrals
                        if second.referrer == referral.referred
                    ],
                }
                for referral in first_level_referrals
            ],
            "direct_referrals_count": len(first_level_referrals),
            "indirect_referrals_count": len(second_level_referrals),
        }

        logger.info(f"Network: {network}")

        return network


class ManagePlanView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/manage_plan.html"


class RequestWithdrawalView(BaseAccountView, FormView):
    template_name = "accounts/pages/request_withdrawal.html"
    form_class = WithdrawalRequestForm

    def form_valid(self, form):
        WithdrawalRequest.objects.create(
            user=self.request.user,
            amount=form.cleaned_data["amount"],
            payout_destination=form.cleaned_data["payout_destination"],
            payout_type=WithdrawalRequest.PayoutType.CRYPTO,
        )
        messages.success(
            self.request,
            "Your withdrawal request has been submitted successfully. You will receive a confirmation email shortly.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:my_account")


class ContactUsView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/contact_us.html"


class FaqView(BaseAccountView, TemplateView):
    template_name = "accounts/pages/faq.html"


class ReferralProgram(BaseAccountView, TemplateView):
    template_name = "accounts/pages/referral_program.html"
