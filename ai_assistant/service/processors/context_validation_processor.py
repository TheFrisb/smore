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
        logger.info(f"Validating context for prompt context: {prompt_context}")
        prompt_type = prompt_context.prompt_type

        if prompt_type in self.get_league_related_prompt_types():
            logger.info(f"Processing league related prompt: {prompt_type}")

            if not prompt_context.leagues:
                logger.info(f"No leagues found in prompt context: {prompt_context}")
                prompt_context.response = "I couldn't find any leagues in your message. Please provide the league names you want to know about."
                prompt_context.can_proceed = False
                return

            if not prompt_context.league_objs:
                logger.info(
                    f"No league objects found in prompt context: {prompt_context}"
                )
                prompt_context.response = "I couldn't find the leagues you mentioned. Please provide the full league names and perhaps their country to help me find them."
                prompt_context.can_proceed = False
                return

        if prompt_type in self.get_match_related_prompt_types():
            logger.info(f"Processing match related prompt: {prompt_type}")

            if prompt_context.team_names and not prompt_context.team_objs:
                logger.info(
                    f"No team objects found in prompt context: {prompt_context}"
                )
                prompt_context.response = "I couldn't find the teams you mentioned. Please provide the full team names to help me find them."
                prompt_context.can_proceed = False
                return

            if (
                prompt_type == PromptType.SINGLE_MATCH_PREDICTION
                and len(prompt_context.team_objs) < 2
            ):
                logger.info(
                    f"Not enough teams found in prompt context: {prompt_context}"
                )

                prompt_context.response = "I couldn't find the teams you mentioned. Please provide the full team names to help me find them."
                prompt_context.can_proceed = False
                return

        logger.info(f"Context validated for prompt context: {prompt_context}")
