from typing import Dict, Optional

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from notifications.models import NotificationTopic


class FCMService:
    """
    Service for handling Firebase Cloud Messaging (FCM) notifications with
    NotificationTopic integration. Supports sending to topics or individual tokens.
    """

    @staticmethod
    def validate_inputs(
        topic: Optional[str],
        title: str,
        body: str,
        token: Optional[str] = None,
    ) -> Optional[str]:
        """
        Validate notification input parameters.

        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if not title:
            return "Title is required"
        if not body:
            return "Body is required"
        if not (topic or token):
            return "Either topic or token is required"
        if topic and not NotificationTopic.objects.filter(name=topic).exists():
            return f"Topic '{topic}' does not exist"
        return None

    def _build_message(
        self,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        topic: Optional[str] = None,
        token: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> messaging.Message:
        """
        Build an FCM message with notification and optional data payload.
        """
        notification = messaging.Notification(title=title, body=body)
        if token:
            return messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=self._get_andorid_config(),
            )
        elif topic:
            return messaging.Message(
                notification=notification,
                data=data or {},
                topic=topic,
                android=self._get_andorid_config(),
            )
        else:
            raise ValueError("Either topic or token must be provided")

    def send_notification(
        self,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        topic: Optional[str] = None,
        token: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> dict:
        """
        Send a notification to a specific FCM topic or token with validation.
        """
        validation_error = self.validate_inputs(topic, title, body, token)
        if validation_error:
            return {"status": "error", "message": validation_error}

        try:
            message = self._build_message(title, body, data, topic, token, image_url)
            message_id = messaging.send(message)
            return {
                "status": "success",
                "message_id": message_id,
                "topic": topic,
                "token": token,
            }
        except FirebaseError as e:
            return {
                "status": "error",
                "message": f"Firebase error: {str(e)}",
                "error_code": getattr(e, "code", "unknown"),
            }
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

    def send_silent_notification(
        self,
        additional_data: Optional[Dict] = None,
    ) -> dict:
        """
        Send a data-only message to the 'ALL' topic to trigger notification refetch
        in client apps without displaying a visible notification.
        """
        topic = "ALL"
        if not NotificationTopic.objects.filter(name=topic).exists():
            return {"status": "error", "message": f"Topic '{topic}' does not exist"}

        default_data = {"type": "refetch_notifications", "silent": "true"}
        if additional_data:
            default_data.update(additional_data)

        try:
            message = messaging.Message(
                data=default_data, topic=topic, android=self._get_andorid_config()
            )
            message_id = messaging.send(message)
            return {
                "status": "success",
                "message_id": message_id,
                "topic": topic,
            }
        except FirebaseError as e:
            return {
                "status": "error",
                "message": f"Firebase error: {str(e)}",
                "error_code": getattr(e, "code", "unknown"),
            }
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

    def _get_andorid_config(self):
        android_config = messaging.AndroidConfig(
            priority="high",
        )

        return android_config
