import logging
from abc import ABC, abstractmethod
from typing import Optional

from django.conf import settings
from openai import OpenAI

from ai_assistant.service.data import PromptContext, PromptType

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """
    Base class for all processors with LLM client management.
    """

    _client = None  # Class-level client instance

    def __init__(
            self, name: str, llm_model: Optional[str]
    ):  # Use string for model name instead of ChatModel type
        self.name = name
        self.llm_model = llm_model

    @classmethod
    def get_client(cls):
        """Lazy-load singleton client instance with thread-safe initialization"""
        if cls._client is None:
            cls._client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
            )
            logger.info(f"Initialized OpenAI client for {cls.__name__} processors")
        return cls._client

    @property
    def client(self):
        """Accessor for the shared client instance"""
        return self.get_client()

    @abstractmethod
    def process(self, prompt_context: PromptContext):
        """Process the data and return the result"""
        pass

    def get_league_related_prompt_types(self):
        """
        Returns a list of prompt types related to league predictions.
        """
        return [PromptType.SINGLE_LEAGUE_PREDICTION, PromptType.MULTI_LEAGUE_PREDICTION]

    def get_match_related_prompt_types(self):
        """
        Returns a list of prompt types related to match predictions.
        """
        return [
            PromptType.SINGLE_MATCH_PREDICTION,
            PromptType.MULTI_MATCH_PREDICTION,
        ]

    def get_single_match_related_prompt_types(self):
        """
        Returns a list of prompt types related to single match predictions.
        """
        return [
            PromptType.SINGLE_MATCH_PREDICTION
        ]

    def get_multi_match_related_prompt_types(self):
        """
        Returns a list of prompt types related to multi match predictions.
        """
        return [
            PromptType.MULTI_MATCH_PREDICTION,
            PromptType.MULTI_RANDOM_MATCH_PREDICTION,
        ]

    def get_bet_suggestions_prompt_types(self):
        """
        Returns a list of prompt types related to bet suggestions.
        """
        return [
            PromptType.MULTI_RANDOM_MATCH_PREDICTION,
            PromptType.SINGLE_RANDOM_MATCH_PREDICTION,
        ]

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.name}) using {self.llm_model}>"
