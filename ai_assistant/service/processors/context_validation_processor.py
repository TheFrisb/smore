import logging

from ai_assistant.service.data import PromptContext, PromptType
from ai_assistant.service.processors.base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class ContextValidationProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="ContextValidationProcessor", llm_model=None)

    def process(self, prompt_context: PromptContext):
        """
        Validate the context of the prompt.
        """
        logger.info(
            f"[{self.name}] Validating context for prompt context: {prompt_context}"
        )
        prompt_type = prompt_context.prompt_type

        if prompt_type in self.get_bet_suggestions_prompt_types():
            return

        if prompt_type in self.get_match_related_prompt_types():
            if not prompt_context.team_objs:
                logger.error(
                    f"[{self.name}] 0 teams were found for a match related prompt."
                )
                prompt_context.can_proceed = False
                prompt_context.response = "I couldn't match the teams you mentioned. Please provide the full name of the teams."

            if (
                    len(prompt_context.team_objs) < 2
                    and prompt_type == PromptType.SINGLE_MATCH_PREDICTION
            ):
                logger.error(
                    f"[{self.name}] 1 team was found for a single match related prompt."
                )
                prompt_context.can_proceed = False
                prompt_context.response = (
                    "Please provide the full name of the teams in the sport match."
                )

            if (
                    len(prompt_context.team_objs) < 2
                    and prompt_type == PromptType.MULTI_MATCH_PREDICTION
            ):
                logger.error(
                    f"[{self.name}] 1 team was found for a multi match related prompt."
                )
                prompt_context.can_proceed = False
                prompt_context.response = (
                    "Please provide the full name of the teams in the sport matches."
                )

        if prompt_type in self.get_league_related_prompt_types():
            if len(prompt_context.league_objs) < 1:
                logger.error(
                    f"[{self.name}] 0 leagues were found for a league related prompt."
                )
                prompt_context.can_proceed = False
                prompt_context.response = (
                    "Please provide the full name of the leagues in the sport matches."
                )
