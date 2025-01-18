import logging

from django.conf import settings
from mailjet_rest import Client

from accounts.models import WithdrawalRequest
from core.models import SiteSettings

logger = logging.getLogger(__name__)


class MailjetService:
    def __init__(self):
        self.client = Client(
            auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version="v3.1"
        )

    def send_withdrawal_request_email(self, withdrawal_request: WithdrawalRequest):
        logger.info(
            f"Sending withdrawal request email to {withdrawal_request.user.email}"
        )
        site_settings = SiteSettings.get_solo()
        extra_param_1, extra_param_2, extra_param_3, extra_param_4 = "", "", "", ""

        if withdrawal_request.payout_type == WithdrawalRequest.PayoutType.BANK:
            extra_param_1 = f"Full Name: {withdrawal_request.full_name}"
            extra_param_2 = f"Email: {withdrawal_request.email}"
            extra_param_3 = f"Country: {withdrawal_request.country}"
            extra_param_4 = f"IBAN Code: {withdrawal_request.iban}"

        elif withdrawal_request.payout_type == WithdrawalRequest.PayoutType.PAYONEER:
            extra_param_1 = f"Full Name: {withdrawal_request.full_name}"
            extra_param_2 = f"Payoneer Email: {withdrawal_request.email}"
            extra_param_3 = (
                f"Payoneer Customer ID: {withdrawal_request.payoneer_customer_id}"
            )

        else:
            extra_param_1 = (
                f"Bitcoin Address: {withdrawal_request.cryptocurrency_address}"
            )

        data = {
            "Messages": [
                {
                    "From": {"Email": "info@smore.bet", "Name": "SMORE"},
                    "To": [
                        {
                            "Email": withdrawal_request.user.email,
                            "Name": withdrawal_request.user.username,
                        },
                        {
                            "Email": site_settings.notification_email,
                            "Name": "SMORE",
                        },
                    ],
                    "TemplateID": site_settings.customer_withdrawal_request_template_id,
                    "TemplateLanguage": True,
                    "Subject": "Withdrawal Request Received",
                    "Variables": {
                        "extra_param4": extra_param_4,
                        "extra_param3": extra_param_3,
                        "extra_param2": extra_param_2,
                        "extra_param1": extra_param_1,
                        "amount": f"${str(withdrawal_request.amount)}",
                        "payout_type": withdrawal_request.get_payout_type_display(),
                        "username": withdrawal_request.user.username,
                    },
                }
            ]
        }

        self.send_mail(data)

    def send_email_confirmation_email(self, user, confirmation_link):
        logger.info(f"Sending email confirmation email to {user.email}")
        site_settings = SiteSettings.get_solo()
        data = {
            "Messages": [
                {
                    "From": {"Email": "info@smore.bet", "Name": "SMORE"},
                    "To": [{"Email": user.email, "Name": user.username}],
                    "TemplateID": site_settings.email_confirmation_template_id,
                    "TemplateLanguage": True,
                    "Subject": "Please confirm your email",
                    "Variables": {
                        "confirmation_link": confirmation_link,
                        "username": user.username,
                    },
                }
            ]
        }

        self.send_mail(data)

    def send_reset_password_email(self, user, reset_link):
        logger.info(f"Sending reset password email to {user.email}")
        site_settings = SiteSettings.get_solo()
        data = {
            "Messages": [
                {
                    "From": {"Email": "info@smore.bet", "Name": "SMORE"},
                    "To": [{"Email": user.email, "Name": user.username}],
                    "TemplateID": 6649156,
                    "TemplateLanguage": True,
                    "Subject": "Please confirm your email",
                    "Variables": {
                        "link": reset_link,
                        "username": user.username,
                    },
                }
            ]
        }

        self.send_mail(data)

    def send_mail(self, data):
        try:
            response = self.client.send.create(data=data)
            logger.info(f"Email sent successfully: {response.json()}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
