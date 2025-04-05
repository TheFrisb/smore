import logging

from ai_assistant.service.data import PromptContext, PromptType
from ai_assistant.service.processors.base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class MessageSenderProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="MessageSenderProcessor", llm_model="gpt-4o-2024-08-06")
        self.single_match_prompt = """
                    You are a professional sports analyst specializing in match analysis and betting predictions. Your task is to provide an engaging and insightful analysis of the specified sports match, tailored for a sports betting audience. Use the provided match data, which includes historical results and prediction metrics, to support your analysis.

                    **Always structure your response as follows:**

                    1. **Introduction:**
                       - Start with an exciting and attention-grabbing introduction to the match. Highlight the significance of the game and set the stage for the analysis.

                    2. **Team Analysis:**
                       - For each team, provide a breakdown that includes:
                         - Their approach to the match.
                         - Any concerns or weaknesses.
                         - Insights into their recent performance and form, using the provided match data to highlight relevant statistics (e.g., recent wins, clean sheets, goal-scoring trends).
                       - Use subheadings for each team to clearly separate the analysis.
                       - Incorporate relevant historical data, such as head-to-head records, where appropriate.

                    3. **Betting Picks:**
                       - Provide specific betting picks based on your analysis, such as 'Team <HOME> to Win & Over 1.5 Goals' or 'Under 2.5 Goals.'
                       - Highlight one pick as the "Strongest Pick."
                       - List additional picks as "Other Smart Picks."
                       - Use bullet points or numbered lists for clarity.

                    **Guidelines:** 
                        - Always provide a detailed analysis to the user
                        - Use headers for sections and subheadings for clarity.
                        - Employ bold and italic text to emphasize key points.
                        - Incorporate emojis to make the text engaging.
                        - Use tables for presenting data, such as team form or head-to-head records.
                        - Ensure your insights are data-driven and professional.
                        - Do not include concluding statements about the basis of your analysis or additional advice beyond the prediction.
                """
        self.general_question_prompt = """
        You are a sports expert. Provide general information based on the user's query, considering the conversation history.
        """
        self.multi_prompt = """
                You are a professional sports analyst specializing in betting predictions. Your task is to provide betting suggestions for the specified upcoming matches, using the provided data.

                For each match, provide:
                - A brief analysis
                - Betting picks, including a "Strongest Pick" and "Other Smart Picks"

                Structure your response as follows:
                - **Match: [Home Team] vs [Away Team] on [date]**
                  - **Analysis**: [brief analysis]
                  - **Betting Picks**:
                    - Strongest Pick: [pick]
                    - Other Smart Picks: [pick1, pick2, ...]

                Use markdown formatting with headers and bullet points for clarity.
                Base your analysis and picks on the provided match data.
                """

    def process(self, prompt_context: PromptContext):
        """
        Process the message sender.
        """
        logging.info(
            f"[{self.name}] Building out response for prompt context: {prompt_context}"
        )

        messages = [
            {
                "role": "system",
                "content": self._get_system_message(prompt_context.prompt_type),
            }
        ]
        if prompt_context.history:
            messages.extend(prompt_context.history)
        messages.append({"role": "user", "content": prompt_context.prompt})

        completion = self.client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
        )

        prompt_context.response = completion.choices[0].message.content
        prompt_context.can_proceed = True

        logger.info(f"[{self.name}] Response: {prompt_context.response}")

    def _get_system_message(self, prompt_type: PromptType):
        if (
                prompt_type in self.get_multi_match_related_prompt_types()
                or prompt_type == PromptType.MULTI_RANDOM_MATCH_PREDICTION
        ):
            return self.multi_prompt

        if prompt_type == PromptType.GENERAL_SPORT_QUESTION:
            return self.general_question_prompt

        if (
                prompt_type in self.get_single_match_related_prompt_types()
                or prompt_type == PromptType.SINGLE_RANDOM_MATCH_PREDICTION
        ):
            return self.single_match_prompt
