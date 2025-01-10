from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse
from django.views.generic import TemplateView


# Create your views here.
class LoginUserView(LoginView):
    template_name = "accounts/pages/login.html"
    page_title = "Login"

    def get_success_url(self):
        return self.request.GET.get("next", reverse("accounts:my_account"))


class LogoutUserView(LogoutView):
    next_page = "core:home"
    page_title = "Logout"


class RegisterUserView(TemplateView):
    template_name = "accounts/pages/register.html"


class MyAccountView(TemplateView):
    template_name = "accounts/pages/my_account.html"


class MyNetworkView(TemplateView):
    template_name = "accounts/pages/my_network.html"


class ManagePlanView(TemplateView):
    template_name = "accounts/pages/manage_plan.html"


class RequestWithdrawalView(TemplateView):
    template_name = "accounts/pages/request_withdrawal.html"


class ContactUsView(TemplateView):
    template_name = "accounts/pages/contact_us.html"


class FaqView(TemplateView):
    template_name = "accounts/pages/faq.html"
