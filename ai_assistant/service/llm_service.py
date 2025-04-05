import logging

from accounts.models import User
from ai_assistant.models import Message
from ai_assistant.service.data import PromptContext
from ai_assistant.service.processors.context_validation_processor import (
    ContextValidationProcessor,
)
from ai_assistant.service.processors.league_processor import LeagueProcessor
from ai_assistant.service.processors.message_history_processor import (
    MessageHistoryProcessor,
)
from ai_assistant.service.processors.message_sender_processor import MessageSenderProcessor
from ai_assistant.service.processors.prompt_classifier import PromptClassifier
from ai_assistant.service.processors.sport_match_processor import SportMatchProcessor
from ai_assistant.service.processors.team_processor import TeamProcessor

logger = logging.getLogger(__name__)


class LLMService:
    """Service class for handling interactions with the LLM (Language Model)."""

    def __init__(self, user: User, prompt: str):
        self.context = PromptContext(user=user, prompt=prompt)

    def process_prompt(self, prompt: str) -> str:
        user_message = Message.objects.create(
            user=self.context.user,
            message=prompt,
            direction=Message.Direction.OUTBOUND,
        )
        for processor in self.get_processor_list():
            processor().process(self.context)

            if not self.context.can_proceed:
                logger.error(f"Error processing prompt: {self.context.response}")
                return self.context.response

        ai_message = Message.objects.create(
            user=self.context.user,
            message=self.context.response,
            direction=Message.Direction.INBOUND,
        )

        return self.context.response

    def get_processor_list(self):
        """
        Returns a list of all available processors.
        """
        return [
            MessageHistoryProcessor,
            PromptClassifier,
            LeagueProcessor,
            TeamProcessor,
            ContextValidationProcessor,
            SportMatchProcessor,
            MessageSenderProcessor
        ]
