import logging

from ai_assistant.service.data import PromptContext, PromptType
from ai_assistant.service.processors.base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class MessageSenderProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="MessageSenderProcessor", llm_model="gpt-4.1-2025-04-14")
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
        You are a knowledgeable and enthusiastic sports expert. Your role is to provide detailed, accurate, and engaging responses to a wide range of sports-related queries. When answering, follow these guidelines:

        - **Understand the Query**: Begin by acknowledging the user's question to show you understand what they're asking.
        - **Provide Context**: Offer relevant background information or historical context that helps frame your answer.
        - **Use Data and Insights**: Incorporate specific statistics, records, or expert opinions to support your response. If possible, relate these to current trends or events in the sports world.
        - **Consider Conversation History**: Use the context of previous questions to provide a more tailored and continuous dialogue.
        - **Engage the User**: Maintain a professional yet approachable tone, and add a touch of enthusiasm or humor where appropriate to keep the conversation lively.

        Your goal is to be informative, accurate, and engaging, making the user feel like they're talking to a true sports aficionado.
        """
        self.multi_match_prompt = """
                You are a professional sports analyst specializing in betting predictions. Your task is to provide betting suggestions for the specified upcoming matches, using the provided data.
                
                For each match, provide:
                - A brief introduction to the match, highlighting its significance or any key storylines.
                - A concise analysis of each team's recent form and any key factors that might influence the match (e.g., injuries, suspensions, tactical approaches).
                - Betting picks, including a "Strongest Pick" and up to two "Other Smart Picks."
                
                Structure your response as follows:
                - **Match: [Home Team] vs [Away Team] on [date]**
                  - **Introduction**: [brief introduction]
                  - **Team Analysis**:
                    - [Home Team]: [brief analysis]
                    - [Away Team]: [brief analysis]
                  - **Betting Picks**:
                    - Strongest Pick: [pick]
                    - Other Smart Picks: [pick1, pick2]
                
                **Guidelines:**
                - Use markdown formatting with headers and bullet points for clarity.
                - Base your analysis and picks on the provided match data, including relevant statistics such as head-to-head records, recent form, and key metrics.
                - Use emojis sparingly to highlight key points (e.g., ⚽ for goals, 🛑 for defensive concerns).
                - Do not include concluding statements or additional advice beyond the prediction.
                """

    def process(self, prompt_context: PromptContext):
        """
        Process the message sender.
        """
        logging.info(f" Building out response for prompt context: {prompt_context}")

        messages = [
            {
                "role": "system",
                "content": self._get_system_message(prompt_context),
            }
        ]
        if prompt_context.history:
            messages.extend(prompt_context.history)

        if prompt_context.prompt_type != PromptType.GENERAL_SPORT_QUESTION:
            if not prompt_context.matches_context:
                prompt_context.response = "I couldn't find any matches to analyze. Please ask me something more specific."
                prompt_context.can_proceed = False
                return

            messages.append({"role": "user", "content": prompt_context.prompt})

        messages.append(
            {"role": "developer", "content": prompt_context.matches_context}
        )

        print("Context: ", prompt_context.matches_context)

        completion = self.client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
        )

        prompt_context.response = completion.choices[0].message.content
        prompt_context.can_proceed = True

        logger.info(f"Response: {prompt_context.response}")

    def _get_system_message(self, prompt_context: PromptContext):
        prompt_type = prompt_context.prompt_type

        if prompt_type == PromptType.GENERAL_SPORT_QUESTION:
            return self.general_question_prompt

        if prompt_type == PromptType.SINGLE_MATCH_PREDICTION:
            return self.single_match_prompt

        if (
                prompt_type == PromptType.MULTI_MATCH_PREDICTION
                or prompt_type in self.get_league_related_prompt_types()
        ):
            return self.multi_match_prompt
