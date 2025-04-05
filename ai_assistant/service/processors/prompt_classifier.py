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

        **Task:** Classify the user's sports-related prompt and extract entities (teams, leagues, dates).
        Expand abbreviations to full official names (e.g., "PSG" → "Paris Saint-Germain", "ecl" -> "UEFA Champions League").
        Use the current date, {self.get_current_date_time()}, to convert the user specified dates (e.g., "tomorrow") relative to the current date to ISO 8601 format (YYYY-MM-DD).
        Leverage conversation history when the user's prompt is not direct by itself to extract the data the user wants to refer to (e.g., "Give me another prediction for that match" refers to the last match mentioned in the conversation).

        **Output Format:** Return a dictionary with:
        - `prompt_type`: Exact type from the allowed list.
        - `team_names`: List of full team names.
        - `league_names`: List of full league names.
        - `suggested_dates`: List of relevant dates (or empty if unspecified).

        **Allowed Prompt Types:**
        - `SINGLE_MATCH_PREDICTION`: User is asking for a single match prediction (e.g., "Give me a match prediction for PSG vs Real Madrid").
        - `MULTI_MATCH_PREDICTION`: User is asking for 2 or more match predictions (e.g., "Give me a prediction for PSG vs Real Madrid and Chelsea vs Arsenal", "Give me some match predictions for PSG, Tottenham, man utd").
        - `SINGLE_LEAGUE_PREDICTION`: User is asking for predictions in a specific league (e.g., "Give me a prediction for the Premier League").
        - `MULTI_LEAGUE_PREDICTION`: User is asking for predictions in multiple leagues (e.g., "Give me some predictions for the Premier League and La Liga").
        - `GENERAL_SPORT_QUESTION`: Other sports-related questions that don't fit the above categories (e.g., "Who is the best player in the NBA?").
        - `NOT_SPORT_RELATED`: Non-sports queries.

        **Additional Prompt Type Classification Guide:**
        - If the user asks for predictions or bets about a sport match without specifying teams or leagues and the user is asking for a single match (e.g.. "Give me a match prediction", "Give me a detailed match analysis"), classify the user's prompt as `SINGLE_MATCH_PREDICTION`. 
        - If the user asks for predictions or bets about a sport match without specifying teams or leagues and the user is asking for predictions or bets about multiple matches without specifying teams or leagues (e.g., "Give me some match predictions", "Give me some bets to play today"), classify the user's prompt as `MULTI_MATCH_PREDICTION`. 
        - If leagues are mentioned without teams, classify as `SINGLE_LEAGUE_PREDICTION` (specific league mentioned) or `MULTI_LEAGUE_PREDICTION` (user  is asking for a result for more than 1 league).
        - For sport related general questions, classify as `GENERAL_SPORT_QUESTION`.
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
           **Response:** {{'prompt_type': 'MULTI_MATCH_PREDICTION', 'team_names': [], 'league_names': [], 'suggested_dates': []}}

        2. **User:** "Predict the Manchester United vs Liverpool match tomorrow"  
           **Response:** {{'prompt_type': 'SINGLE_MATCH_PREDICTION', 'team_names': ['Manchester United', 'Liverpool'], 'league_names': [], 'suggested_dates': ['2024-03-11']}}

        3. **User:** "Give me predictions for Chelsea vs Arsenal and Tottenham vs Manchester City this weekend"  
           **Response:** {{'prompt_type': 'MULTI_MATCH_PREDICTION', 'team_names': ['Chelsea', 'Arsenal', 'Tottenham', 'Manchester City'], 'league_names': [], 'suggested_dates': ['2024-03-16', '2024-03-17']}}

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
            logger.info(f"Processing prompt: {prompt_context.prompt}")

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
            logger.info(f"Finished processing prompt with result: {event}")

            prompt_context.prompt_type = event.prompt_type
            prompt_context.team_names = event.team_names
            prompt_context.league_names = event.league_names

            if hasattr(event, "suggested_dates"):
                for date_str in event.suggested_dates:
                    parsed_datetime = self._parse_datetime(date_str)
                    if parsed_datetime:
                        prompt_context.suggested_dates.append(parsed_datetime.date())

        except Exception as e:
            logger.error(f" Error processing prompt: {e}")
            prompt_context.can_proceed = False
            prompt_context.response = (
                "An unexpected error has occurred. Please try again."
            )

        if prompt_context.prompt_type == PromptType.NOT_SPORT_RELATED:
            prompt_context.can_proceed = False
            prompt_context.response = "I specialize in sport match analysis and predictions. Please provide a specific match or a general sports question."

        logger.info(f"Prompt classification result: {prompt_context}")

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
