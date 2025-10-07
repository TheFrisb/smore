from typing import Tuple
from django.conf import settings

from accounts.models import User
from ai_assistant.models import Message
from subscriptions.models import Product

AI_PRODUCT_NAME = Product.Names.AI_ANALYST
FREE_MESSAGES_LIMIT = 3


class AIUsagePolicy:
    @staticmethod
    def outbound_message_count(user) -> int:
        return Message.objects.filter(
            user=user, direction=Message.Direction.OUTBOUND
        ).count()

    @classmethod
    def can_use_ai(cls, user: User) -> Tuple[bool, int]:
        """
        Returns (can_use: bool, current_outbound_count: int)
        Policy:
          - If user has an active subscription to the AI product -> allowed
          - Otherwise: allowed while outbound_count < FREE_MESSAGES_LIMIT
        """
        if not user or not user.is_authenticated:
            return False, 0

        if user.has_access_to_product(AI_PRODUCT_NAME):
            return True, cls.outbound_message_count(user)

        count = cls.outbound_message_count(user)
        return (count < FREE_MESSAGES_LIMIT), count
