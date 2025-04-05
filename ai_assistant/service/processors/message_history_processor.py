import logging

from accounts.models import User
from ai_assistant.models import Message
from ai_assistant.service.data import PromptContext
from ai_assistant.service.processors.base_processor import BaseProcessor

logging = logging.getLogger(__name__)


class MessageHistoryProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(
            name="MessageHistoryProcessor", llm_model=None
        )

    def process(self, prompt_context: PromptContext):
        """
        Fetches the user's message history, and adds it to the context.
        """
        user = prompt_context.user

        if not user:
            logging.warn(
                f"[{self.name}] No user found in the prompt context. Skipping message history fetch."
            )
            return

        logging.info(f"[{self.name}] Processing message history for user {user.id}")

        messages = self._fetch_user_conversation(user)

        logging.info(
            f"[{self.name}] Fetched {len(messages)} messages for user {user.id}. Messages: {messages}"
        )

        prompt_context.history = messages

    def _fetch_user_conversation(self, user: User):
        """
        Fetches the user's message history from the database.
        """
        logging.info(f"[{self.name}] Fetching user conversation for user {user.id}")
        recent_messages = Message.objects.filter(user=user).order_by("-created_at")[:10]
        direction_map = {
            Message.Direction.OUTBOUND: "user",
            Message.Direction.INBOUND: "assistant",
        }

        return [
            {
                "role": direction_map[msg.direction],
                "content": f"[{msg.created_at}] {msg.message}",
            }
            for msg in reversed(recent_messages)
        ]
