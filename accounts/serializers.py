from rest_framework import serializers

from accounts.forms.withdrawal_request_form import is_valid_btc_address
from accounts.models import WithdrawalRequest, UserSubscription, User
from core.models import Product


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = WithdrawalRequest
        fields = "__all__"

    def validate(self, data):
        payout_type = data.get("payout_type")

        if payout_type == WithdrawalRequest.PayoutType.CRYPTOCURRENCY:
            if not data.get("cryptocurrency_address"):
                raise serializers.ValidationError(
                    {"cryptocurrency_address": "Please provide a bitcoin address."}
                )

            if not is_valid_btc_address(data.get("cryptocurrency_address")):
                raise serializers.ValidationError(
                    {
                        "cryptocurrency_address": "The bitcoin address you've provided is invalid."
                    }
                )

        elif payout_type == WithdrawalRequest.PayoutType.BANK:
            if not data.get("full_name"):
                raise serializers.ValidationError(
                    {"full_name": "Please provide your full name."}
                )

            # check if full name contains at least 2 words
            if len(data.get("full_name").split()) < 2:
                raise serializers.ValidationError(
                    {"full_name": "Please provide your full name."}
                )

            if not data.get("iban"):
                raise serializers.ValidationError(
                    {"iban": "Please provide your IBAN code."}
                )

            if not data.get("email"):
                raise serializers.ValidationError(
                    {"email": "Please provide your email."}
                )

            if not data.get("country"):
                raise serializers.ValidationError(
                    {"country": "Please provide your country."}
                )

        if data.get("amount") <= 0:
            raise serializers.ValidationError(
                {"amount": "Please provide a valid amount."}
            )

        if data.get("user").available_balance < data.get("amount"):
            raise serializers.ValidationError(
                {"amount": "You don't have enough balance to make this withdrawal."}
            )

        return data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "analysis_per_month"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = UserSubscription
        fields = ["status", "frequency", "price", "start_date", "end_date", "products"]


class UserSerializer(serializers.ModelSerializer):
    user_subscription = UserSubscriptionSerializer(
        source="subscription", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_email_verified",
            "user_subscription",
            "first_name",
            "last_name",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "is_email_verified",
            "user_subscription",
            "first_name",
            "last_name",
        ]
