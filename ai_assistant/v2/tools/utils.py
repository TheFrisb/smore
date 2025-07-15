from datetime import datetime

from django.utils import timezone
from langchain_core.tools import tool


@tool
def get_current_time() -> datetime:
    """
    Get the current time in UTC.

    Returns:
        datetime: The current time in UTC.
    """
    return timezone.now()
