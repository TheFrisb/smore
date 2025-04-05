import logging
from datetime import datetime
from typing import Optional

from ai_assistant.service.data import PromptContext, PromptClassifierModel, PromptType
from ai_assistant.service.processors.base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class PromptClassifier(BaseProcessor):
    def __init__(self):
        super().__init__(name="PromptClassifier", llm_model="gpt-4o-mini-2024-07-18")
        self.system_prompt = f"""
        **Role:** You are a sports conversation analyst AI.

        **Task:** Classify the user's sports-related prompt and extract entities (teams, leagues, dates). Expand abbreviations to full official names (e.g., "PSG" → "Paris Saint-Germain"). Use the current date, {self.get_current_date_time()}, to convert relative dates (e.g., "tomorrow") to ISO 8601 format (YYYY-MM-DD). Leverage conversation history only when the prompt refers to previous messages (e.g., "that match").

        **Output Format:** Return a dictionary with:
        - `prompt_type`: Exact type from the allowed list.
        - `team_names`: List of full team names.
        - `league_names`: List of full league names.
        - `suggested_dates`: List of relevant dates (or empty if unspecified).

        **Allowed Prompt Types:**
        - `SINGLE_MATCH_PREDICTION`: User is asking for a specific match prediction for 2 specified teams.
        - `MULTI_MATCH_PREDICTION`: User is asking for multiple match predictions for 2 or more specified teams.
        - `SINGLE_LEAGUE_PREDICTION`: User is asking for a specific league prediction (e.g., "Give me a prediction for the Premier League").
        - `MULTI_LEAGUE_PREDICTION`: User is asking for multiple league predictions (e.g., "Give me a prediction for the Premier League and La Liga").
        - `SINGLE_RANDOM_MATCH_PREDICTION`: User is asking for any random match prediction (e.g., "Give me a match prediction").
        - `MULTI_RANDOM_MATCH_PREDICTION`: User is asking for multiple random match predictions (e.g., "Give me some match predictions").
        - `GENERAL_SPORT_QUESTION`: Other sports-related questions.
        - `NOT_SPORT_RELATED`: Non-sports queries.

        **Classification Rules:**
        - If the prompt requests predictions or bets without specific teams or leagues (e.g., "give me some bet predictions"), classify as `MULTI_RANDOM_MATCH_PREDICTION`.
        - If specific teams are mentioned, classify as `SINGLE_MATCH_PREDICTION` (one match) or `MULTI_MATCH_PREDICTION` (multiple matches).
        - If leagues are mentioned without teams, classify as `SINGLE_LEAGUE_PREDICTION` or `MULTI_LEAGUE_PREDICTION`.
        - For unclear sports-related intents, use `GENERAL_SPORT_QUESTION`.
        - For non-sports prompts, use `NOT_SPORT_RELATED`.

        **General Rules:**
        - Expand abbreviations (e.g., "UCL" → "UEFA Champions League").
        - Convert relative dates:
          - "today" → current date.
          - "tomorrow" → current date + 1 day.
          - "next <day>" → next occurrence after current date.
          - "this weekend" → upcoming Saturday and Sunday.
          - Vague terms (e.g., "next week") → empty `suggested_dates` unless specified.

        **Examples (assume current date is 2024-03-10):**
        1. **User:** "Give me some bet predictions"  
           **Response:** {{'prompt_type': 'MULTI_RANDOM_MATCH_PREDICTION', 'team_names': [], 'league_names': [], 'suggested_dates': []}}

        2. **User:** "Predict the Manchester United vs Liverpool match tomorrow"  
           **Response:** {{'prompt_type': 'SINGLE_MATCH_PREDICTION', 'team_names': ['Manchester United', 'Liverpool'], 'league_names': [], 'suggested_dates': ['2024-03-11']}}

        3. **User:** "Give me predictions for Chelsea vs Arsenal and Tottenham vs Manchester City this weekend"  
           **Response:** {{'prompt_type': 'MULTI_MATCH_PREDICTION', 'team_names': ['Chelsea', 'Arsenal', 'Tottenham Hotspur', 'Manchester City'], 'league_names': [], 'suggested_dates': ['2024-03-16', '2024-03-17']}}

        4. **User:** "What are the predictions for the Premier League this week?"  
           **Response:** {{'prompt_type': 'SINGLE_LEAGUE_PREDICTION', 'team_names': [], 'league_names': ['Premier League'], 'suggested_dates': []}}

        5. **User:** "Give me another prediction for that match" *(Previous: "Predict PSG vs Real Madrid")*  
           **Response:** {{'prompt_type': 'SINGLE_MATCH_PREDICTION', 'team_names': ['Paris Saint-Germain', 'Real Madrid'], 'league_names': [], 'suggested_dates': []}}

        6. **User:** "Who’s the best player in the NBA?"  
           **Response:** {{'prompt_type': 'GENERAL_SPORT_QUESTION', 'team_names': [], 'league_names': ['National Basketball Association'], 'suggested_dates': []}}

        7. **User:** "What’s the weather like?"  
           **Response:** {{'prompt_type': 'NOT_SPORT_RELATED', 'team_names': [], 'league_names': [], 'suggested_dates': []}}
        """

    def process(self, prompt_context: PromptContext):
        try:
            logger.info(f"[{self.name}] Processing prompt: {prompt_context.prompt}")

            messages = [{"role": "system", "content": self.system_prompt}]
            if prompt_context.history:
                messages.extend(prompt_context.history)
            messages.append({"role": "user", "content": prompt_context.prompt})

            completion = self.client.beta.chat.completions.parse(
                model=self.llm_model,
                messages=messages,
                response_format=PromptClassifierModel,
            )

            event = completion.choices[0].message.parsed
            logger.info(
                f"[{self.name}] Finished processing prompt with result: {event}"
            )

            prompt_context.prompt_type = event.prompt_type
            prompt_context.team_names = event.team_names
            prompt_context.league_names = event.league_names

            if event.prompt_type in [PromptType.SINGLE_MATCH_PREDICTION,
                                     PromptType.MULTI_MATCH_PREDICTION] and not event.team_names:
                logger.warn(f"[{self.name}] No teams found for match prediction prompt. Switching to random prediction")
                prompt_context.prompt_type = PromptType.MULTI_RANDOM_MATCH_PREDICTION

            if hasattr(event, "suggested_dates"):
                for date_str in event.suggested_dates:
                    parsed_datetime = self._parse_datetime(date_str)
                    if parsed_datetime:
                        prompt_context.suggested_dates.append(parsed_datetime.date())

        except Exception as e:
            logger.error(f"[{self.name}] Error processing prompt: {e}")
            prompt_context.can_proceed = False
            prompt_context.response = (
                "An unexpected error has occurred. Please try again."
            )

        if prompt_context.prompt_type == PromptType.NOT_SPORT_RELATED:
            prompt_context.can_proceed = False
            prompt_context.response = "I specialize in sport match analysis and predictions. Please provide a specific match or a general sports question."

        logger.info(f"[{self.name}] Prompt classification result: {prompt_context}")

    def get_current_date_time(self):
        # return current date with day name
        current_date = datetime.now()
        return current_date.strftime("%Y-%m-%d %A")

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.
        This method should be overridden in subclasses to provide specific parsing logic.
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.error(f"{self.name}: Failed to parse date string: {date_str}")
            return None
