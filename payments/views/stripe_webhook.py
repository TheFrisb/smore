import stripe
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from payments.services.stripe_webhook_service import StripeWebhookService


logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    stripe_service = StripeWebhookService()
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe_service.process_stripe_event(payload, sig_header)
    except ValueError:
        logger.error("Invalid payload")
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return HttpResponse("Invalid signature", status=400)

    return JsonResponse({"status": "success"})
