import logging
from decimal import Decimal

from django.core.management import BaseCommand

from accounts.models import UserSubscription
from core.models import Product
from payments.services.stripe_price_service import StripePriceService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create subscription prices (weekly, monthly, three_monthly, yearly) for products"

    def handle(self, *args, **options):
        stripe_price_service = StripePriceService()

        products = Product.objects.filter(
            name__in=[Product.Names.SOCCER, Product.Names.BASKETBALL]
        )

        # Price amounts are expressed in cents (smallest currency unit).
        # e.g. 4999 = €49.99
        for product in products:
            if product.name == Product.Names.SOCCER:
                price_config = {
                    UserSubscription.Frequency.WEEKLY: (4999, 3999),
                    UserSubscription.Frequency.THREE_MONTHLY: (26999, 23999),
                }
            else:  # Basketball (fallback)
                price_config = {
                    UserSubscription.Frequency.WEEKLY: (3599, 2599),
                    UserSubscription.Frequency.THREE_MONTHLY: (15999, 139999),
                }

            for interval, (base_cents, discounted_cents) in price_config.items():
                try:
                    self.create_interval_prices(
                        product=product,
                        interval=interval,
                        base_cents=base_cents,
                        discounted_cents=discounted_cents,
                        stripe_price_service=stripe_price_service,
                    )
                except Exception:
                    logger.exception(
                        "Failed to create prices for product=%s interval=%s",
                        getattr(product, "id", product),
                        interval,
                    )

    def create_interval_prices(
        self,
        product,
        interval: str,
        base_cents: int,
        discounted_cents: int,
        stripe_price_service: StripePriceService,
    ):
        """
        Create EUR and CHF prices (base + discounted) for the given product and interval.

        - base_cents, discounted_cents: integers representing smallest currency unit (cents / rappen)
        - interval: string matching UserSubscription.Frequency value (e.g. "weekly", "three_monthly")
        """

        # Nicely formatted interval label: "three_monthly" -> "Three Monthly"
        interval_label = interval.replace("_", " ").title()
        product_label = product.name.capitalize()

        # Create EUR base price
        eur_base = stripe_price_service.create_price(
            product=product,
            nickname=f"{interval_label} - {product_label}",
            amount=base_cents,
            interval=interval,
            currency="eur",
        )

        # Create EUR discounted price
        eur_discount = stripe_price_service.create_price(
            product=product,
            nickname=f"Discounted {interval_label} - {product_label}",
            amount=discounted_cents,
            interval=interval,
            currency="eur",
        )

        # Create CHF base price
        chf_base = stripe_price_service.create_price(
            product=product,
            nickname=f"{interval_label} - {product_label}",
            amount=base_cents,
            interval=interval,
            currency="chf",
        )

        # Create CHF discounted price
        chf_discount = stripe_price_service.create_price(
            product=product,
            nickname=f"Discounted {interval_label} - {product_label}",
            amount=discounted_cents,
            interval=interval,
            currency="chf",
        )

        # Convert cents to Decimal (major currency unit)
        base_decimal = Decimal(base_cents) / Decimal(100)
        discounted_decimal = Decimal(discounted_cents) / Decimal(100)

        # Numeric field names for product (these exist in your model)
        numeric_field = f"{interval}_price"
        discounted_field = f"discounted_{interval}_price"

        # Stripe ID field names:
        # - base normal: {interval}_price_stripe_id
        # - base switzerland: {interval}_switzerland_price_stripe_id
        # - discounted normal: discounted_{interval}_price_stripe_id
        # - discounted switzerland: discounted_switzerland_{interval}_price_stripe_id
        numeric_id_field = f"{interval}_price_stripe_id"
        switzerland_numeric_id_field = f"{interval}_switzerland_price_stripe_id"
        discounted_id_field = f"discounted_{interval}_price_stripe_id"
        switzerland_discounted_id_field = (
            f"discounted_switzerland_{interval}_price_stripe_id"
        )

        # Assign numeric values (major units) if product has those attributes.
        for field_name, value in [
            (numeric_field, base_decimal),
            (discounted_field, discounted_decimal),
        ]:
            if hasattr(product, field_name):
                setattr(product, field_name, value)
            else:
                logger.warning(
                    "Product (id=%s) missing numeric field: %s", product.id, field_name
                )

        # Assign Stripe IDs (we assume the stripe create call returns object with .id)
        assignments = [
            (numeric_id_field, eur_base),
            (discounted_id_field, eur_discount),
            (switzerland_numeric_id_field, chf_base),
            (switzerland_discounted_id_field, chf_discount),
        ]

        for field_name, stripe_obj in assignments:
            if hasattr(product, field_name):
                stripe_id = getattr(stripe_obj, "id", None)
                if stripe_id is None:
                    logger.warning(
                        "Stripe price object missing id for field %s (product=%s)",
                        field_name,
                        product.id,
                    )
                setattr(product, field_name, stripe_id)
            else:
                logger.warning(
                    "Product (id=%s) missing stripe-id field: %s",
                    product.id,
                    field_name,
                )

        product.save()

        logger.info(
            "Created prices for product=%s interval=%s (eur_base=%s eur_discount=%s chf_base=%s chf_discount=%s)",
            product.id,
            interval,
            getattr(eur_base, "id", None),
            getattr(eur_discount, "id", None),
            getattr(chf_base, "id", None),
            getattr(chf_discount, "id", None),
        )
