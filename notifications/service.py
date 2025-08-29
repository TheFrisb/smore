from typing import Dict, Optional

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from notifications.models import NotificationTopic


class FCMService:
    """
    Service for handling Firebase Cloud Messaging (FCM) notifications with
    NotificationTopic integration.
    """

    @staticmethod
    def validate_inputs(topic: str, title: str, body: str) -> Optional[str]:
        """
        Validate notification input parameters.

        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if not topic:
            return "Topic is required"
        if not title:
            return "Title is required"
        if not body:
            return "Body is required"
        if not NotificationTopic.objects.filter(name=topic).exists():
            return f"Topic '{topic}' does not exist"
        return None

    def _build_message(
            self, topic: str, title: str, body: str, data: Optional[Dict] = None
    ) -> messaging.Message:
        """
        Build an FCM message with notification and optional data payload.
        """
        notification = messaging.Notification(title=title, body=body)
        return messaging.Message(
            notification=notification, data=data or {}, topic=topic
        )

    def send_notification(
            self, topic: str, title: str, body: str, data: Optional[Dict] = None
    ) -> dict:
        """
        Send a notification to a specific FCM topic with validation.
        """
        validation_error = self.validate_inputs(topic, title, body)
        if validation_error:
            return {"status": "error", "message": validation_error}

        try:
            message = self._build_message(topic, title, body, data)
            message_id = messaging.send(message)
            return {"status": "success", "message_id": message_id, "topic": topic}
        except FirebaseError as e:
            return {
                "status": "error",
                "message": f"Firebase error: {str(e)}",
                "error_code": getattr(e, "code", "unknown"),
            }
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}
