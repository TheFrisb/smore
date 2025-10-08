from decimal import Decimal

from rest_framework import serializers

from subscriptions.models import Product, BillingProvider


class ProductSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    monthly_price = serializers.SerializerMethodField()
    discounted_monthly_price = serializers.SerializerMethodField()
    yearly_price = serializers.SerializerMethodField()
    discounted_yearly_price = serializers.SerializerMethodField()
    mobile_product_id = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "type",
            "analysis_per_month",
            "monthly_price",
            "discounted_monthly_price",
            "yearly_price",
            "discounted_yearly_price",
            "mobile_product_id",
        ]

    def get_type(self, obj):
        return "SUBSCRIPTION"

    def get_monthly_price(self, obj):
        return "0.00"

    def get_discounted_monthly_price(self, obj):
        return "0.00"

    def get_yearly_price(self, obj):
        return "0.00"

    def get_discounted_yearly_price(self, obj):
        return "0.00"

    def get_mobile_product_id(self, obj):
        return "0"


class AggregatedUserSubscriptionSerializer(serializers.Serializer):
    """
    Serializer for aggregated user subscriptions to mimic the old single subscription structure.
    """

    status = serializers.CharField()
    frequency = serializers.CharField()
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    products = ProductSerializer(many=True)
    first_chosen_product = ProductSerializer()
    provider_type = serializers.CharField()

    def to_representation(self, instance):
        # instance is the User (parent) due to source='*'
        if not instance:
            return None

        user = instance
        active_subs = (
            user.subscriptions.filter(is_active=True)
            .select_related("product_price__product")
            .order_by("start_date")
        )

        if not active_subs.exists():
            return None

        # Collect unique products
        product_ids = active_subs.values_list(
            "product_price__product_id", flat=True
        ).distinct()
        products_data = ProductSerializer(
            Product.objects.filter(id__in=product_ids), many=True
        ).data

        # First chosen product: from the earliest subscription
        first_sub = active_subs.first()
        first_chosen_data = ProductSerializer(first_sub.product_price.product).data

        # Total price: sum of all active subscription prices
        total_price = sum(Decimal(str(sub.product_price.amount)) for sub in active_subs)

        # Status: 'active' for backward compatibility (assuming old used string status)
        status = "active"

        # Frequency: derive from interval and count (assume consistent across subs; take from first)
        frequency = first_sub.product_price.interval.lower() + "ly"

        # Start date: earliest
        start_date = min(sub.start_date for sub in active_subs)

        # End date: latest (to represent overall access period)
        end_date = max(sub.end_date for sub in active_subs)

        # Provider type: assume consistent; take from first (add validation if needed)
        provider_type = (
            first_sub.provider
            if first_sub.provider == BillingProvider.STRIPE
            else "APPLE"
        )
        return {
            "status": status,
            "frequency": frequency,
            "price": total_price,
            "start_date": start_date,
            "end_date": end_date,
            "products": products_data,
            "first_chosen_product": first_chosen_data,
            "provider_type": provider_type,
        }
