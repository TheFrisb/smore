import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_transaction(transaction_id, app_user_id):
    """
    Verify a transaction for a given user.

    Args:
        transaction_id (str): The ID of the transaction to verify.
        user_id (str): The ID of the user who made the transaction.

    Returns:
        bool: True if the transaction is valid, False otherwise.
    """
    url = f"https://api.revenuecat.com/v2/projects/{settings.REVENUECAT_PROJECT_ID}/purchases?store_purchase_identifier={transaction_id}"
    headers = {
        "Authorization": f"Bearer {settings.REVENUECAT_API_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    items_dict = data["items"]

    if not items_dict or len(items_dict) == 0:
        logger.warning(f"No items found for transaction {transaction_id}")
        return False

    purchase = data["items"][0]
    customer_id = (
        int(purchase.get("customer_id")) if purchase.get("customer_id") else None
    )

    logger.info(
        f"CustomerID: {customer_id} for transaction {transaction_id} and user {app_user_id}"
    )

    if customer_id != app_user_id:
        logger.warning(f"Customer ID mismatch: {customer_id} != {app_user_id}")
        return False

    return True
