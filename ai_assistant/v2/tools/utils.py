from django.utils import timezone
from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """
    Use this tool to get the current datetime in UTC before trying to access any time-sensitive data.

    Returns:
        str: The current datetime in ISO 8601 format (e.g., "2025-10-01T12:00:00Z").
    """
    return timezone.now().isoformat()
