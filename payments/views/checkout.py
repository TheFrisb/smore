import logging

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from facebook.services.facebook_pixel import FacebookPixel
from payments.services.stripe_checkout_service import StripeCheckoutService
from subscriptions.models import ProductPrice, BillingProvider

logger = logging.getLogger(__name__)


class CreateSubscriptionCheckoutUrl(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    class InputSerializer(serializers.Serializer):
        product_price = serializers.PrimaryKeyRelatedField(
            queryset=ProductPrice.objects.filter(provider=BillingProvider.STRIPE)
        )

    class OutputSerializer(serializers.Serializer):
        url = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_price = serializer.validated_data["product_price"]
        checkout_session = self.service.create_subscription_checkout_session(
            user=request.user, price_id=product_price.provider_price_id
        )

        self._send_fb_event(product_price.product, checkout_session.amount_total)

        output_serializer = self.OutputSerializer({"url": checkout_session.url})
        return Response(output_serializer.data)

    def _send_fb_event(self, product, amount_total):
        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.initiate_checkout(product, amount_total)
        except Exception as e:
            logger.error(
                f"Error while sending InitiateCheckout Facebook Pixel event: {e}"
            )


class UpdateSubscriptionView(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    #
    # class InputSerializer(serializers.Serializer):
    #     products = serializers.ListField(child=serializers.IntegerField())
    #     frequency = serializers.ChoiceField(choices=UserSubscription.Frequency)
    #     firstProduct = serializers.IntegerField(allow_null=True)
    #
    # def use_discounted_prices(self, products):
    #
    #     return len(products) > 1

    # def post(self, request, *args, **kwargs):
    #     # Check if the user has an active subscription
    #     if not request.user.subscription_is_active:
    #         logger.info(
    #             f"User {request.user.id} attempted to manage subscription without an active subscription."
    #         )
    #         return Response(
    #             status=403,
    #             data={"message": "The user does not have an active subscription."},
    #         )
    #
    #     # Validate input data
    #     serializer = self.InputSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     product_ids = serializer.validated_data["products"]
    #     desired_frequency = serializer.validated_data["frequency"]
    #
    #     # Fetch requested products
    #     products = Product.objects.filter(id__in=product_ids)
    #     first_chosen_product = Product.objects.filter(
    #         id=serializer.validated_data["firstProduct"]
    #     ).first()
    #     if len(products) != len(product_ids):
    #         return Response(
    #             status=400, data={"message": "One or more product IDs are invalid."}
    #         )
    #
    #     if (
    #         serializer.validated_data["firstProduct"]
    #         not in serializer.validated_data["products"]
    #     ):
    #         return Response(
    #             status=400, data={"message": "Invalid 'firstProduct' field."}
    #         )
    #
    #     if not products.exists():
    #         return Response(status=400, data={"message": "No products found."})
    #
    #     # Get the user's current subscription
    #     user_subscription = request.user.subscription
    #     stripe_subscription = self.service.get_stripe_subscription_by_id(
    #         user_subscription.stripe_subscription_id
    #     )
    #
    #     is_switzerland = request.session.get("is_switzerland", False)
    #
    #     # Build price-to-product mapping
    #     all_products = Product.objects.all()
    #     price_to_product = {}
    #     for product in all_products:
    #         price_to_product[product.monthly_price_stripe_id] = product
    #         price_to_product[product.yearly_price_stripe_id] = product
    #         # Include discounted prices if they exist
    #         if product.discounted_monthly_price_stripe_id:
    #             price_to_product[product.discounted_monthly_price_stripe_id] = product
    #         if product.discounted_yearly_price_stripe_id:
    #             price_to_product[product.discounted_yearly_price_stripe_id] = product
    #
    #     # Determine desired price IDs based on frequency
    #     desired_price_ids = {}
    #     for product in products:
    #         use_discounted_prices = self.use_discounted_prices(products)
    #
    #         if product == first_chosen_product:
    #             logger.info(
    #                 f"First chosen product: {product.get_name_display()}, fetching non-discounted price"
    #             )
    #             use_discounted_prices = False
    #         desired_price_ids[product] = product.get_price_id_for_subscription(
    #             desired_frequency, use_discounted_prices, is_switzerland
    #         )
    #
    #     # Process current subscription items
    #     current_items = stripe_subscription["items"]["data"]
    #     items_to_update = []
    #     covered_products = set()
    #
    #     logger.info(f"Current items: {current_items}")
    #     logger.info(f"Desired price ids: {desired_price_ids}")
    #     logger.info(f"Price to product: {price_to_product}")
    #
    #     for item in current_items:
    #         price_id = item["price"]["id"]
    #         logger.info(f"Processing item with price id: {price_id}")
    #
    #         product = price_to_product.get(price_id)
    #         logger.info(f"Matched price id to product: {product.get_name_display()}")
    #         if product and product in products:
    #             # Product remains in subscription, update price if frequency changed
    #             logger.info(
    #                 f"Product {product.get_name_display()} remains in subscription"
    #             )
    #             desired_price_id = desired_price_ids[product]
    #             logger.info(
    #                 f"Product {product.get_name_display()}'s desired price id: {desired_price_id}"
    #             )
    #             items_to_update.append({"id": item["id"], "price": desired_price_id})
    #             covered_products.add(product)
    #         else:
    #             # Product removed, delete the item
    #             logger.info(
    #                 f"Product {product.get_name_display()} removed from subscription"
    #             )
    #             items_to_update.append({"id": item["id"], "deleted": True})
    #
    #     # Add new items for products not currently in subscription
    #     for product in set(products) - covered_products:
    #         items_to_update.append({"price": desired_price_ids[product]})
    #
    #     try:
    #         self.service.modify_stripe_subscription(
    #             user_subscription.stripe_subscription_id, items_to_update
    #         )
    #     except stripe.error.CardError as e:
    #         logger.error(f"Card error while updating subscription: {e}")
    #         return Response(
    #             status=400,
    #             data={
    #                 "message": e.user_message
    #                 or "Your card was declined. Please update your payment method"
    #             },
    #         )
    #     except stripe.error.StripeError as e:
    #         logger.error(f"Stripe error while updating subscription: {e}")
    #         return Response(
    #             status=500,
    #             data={
    #                 "message": "An error occurred while processing your payment. Please try again later"
    #             },
    #         )
    #     return Response({"message": "Subscription updated successfully."})

    def post(self):
        pass
