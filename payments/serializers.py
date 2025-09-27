from rest_framework import serializers

from accounts.models import UserSubscription
from core.models import Product


class ProductInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    frequency = serializers.ChoiceField(choices=UserSubscription.Frequency.choices)

class SubscriptionInputSerializer(serializers.Serializer):
    products = ProductInputSerializer(many=True)