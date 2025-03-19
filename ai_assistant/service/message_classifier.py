import logging
import re
from enum import Enum
from typing import List, Tuple, Optional, Union

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)


class MessageCategory(Enum):
    MATCH_SPECIFIC_REQUEST = "match_specific_request"
    BET_SUGGESTIONS = "bet_suggestions"
    GENERAL_SPORT_INFORMATION = "general_sport_information"
    UNRELATED = "unrelated"


class MessageClassifier:
    def __init__(self, llm):
        self.llm = llm
        self.system_message = SystemMessage(
            content="""
            You are an AI assistant specializing in sports-related conversations, focused on match analyses, betting predictions, and sports updates. Your task is to analyze the current message and the provided conversation history (recent user prompts and AI responses) to determine the user's intent and the relevant sport.

            **Instructions:**
            1. Check if the current message or conversation history relates to sports.
            2. If sports-related, identify the sport (e.g., soccer, basketball, tennis). If the current message doesn’t specify a sport or is vague (e.g., "this match") but refers to prior context (e.g., teams or matches), infer the sport and teams (if applicable) from the history.
            3. Classify the user’s intent into one of these categories:
               - match_specific_request: Queries about a specific match, including betting picks, updates, or follow-ups referring to a match mentioned in the recent history.
               - bet_suggestions: General requests for betting tips or match recommendations that don’t specify a match and do not refer to a specific match in the history.
               - general_sport_information: Broad sports questions not tied to a specific match or betting (e.g., rules, stats, team histories).
               - unrelated: Messages unrelated to sports, with no sports context in the history.

            **Rules:**
            - If the message names two teams (e.g., "Barcelona vs Manchester United"), classify as 'match_specific_request'.
            - If the message is vague (e.g., "What about other picks?", "Any updates?") and the recent history mentions a specific match, classify as 'match_specific_request', inferring the match from the history.
            - If the message asks for betting tips or recommendations without specifying a match, and no specific match exists in the recent history that the message can be referred contextually, classify as 'bet_suggestions'.
            - If the message covers general sports topics without mentioning a match or betting, classify as 'general_sport_information'.
            - If no sports context is present in the message or history, classify as 'unrelated'.
            - Use only the listed categories. Do not create new ones or add extra text.

            **Examples:**
            - Message: "What’s the best matches to play today?"
              Category: bet_suggestions
              Sport: soccer

            - Message: "Give me a betting pick for Barcelona vs Manchester United"
              Category: match_specific_request
              Sport: soccer

            - History: "Tell me about Barcelona vs Manchester United"
              Current message: "What about other picks?"
              Category: match_specific_request
              Sport: soccer

            - History: "What’s the Premier League schedule?"
              Current message: "Any good bets today?"
              Category: bet_suggestions
              Sport: soccer

            - Message: "Who’s the best basketball player?"
              Category: general_sport_information
              Sport: basketball

            - Message: "How’s the stock market?"
              Category: unrelated
              Sport: N/A
              
            - Message: "Netherlands vs Spain"
              Category: match_specific_request
              Sport: N/A

            **Output Format:**
            Category: [category]
            Sport: [sport name if applicable, otherwise N/A]
            """
        )

    def classify(
        self, message: str, history: List[Union[HumanMessage, AIMessage]]
    ) -> Tuple[MessageCategory, Optional[str]]:
        try:
            full_message_list = (
                [self.system_message] + history + [HumanMessage(content=message)]
            )
            response = self.llm.invoke(full_message_list)
            response_text = response.content.strip()
            logger.info(f"Raw classification response: {response_text}")

            # Parse with regex
            category_match = re.search(
                r"Category:\s*(\w+)", response_text, re.IGNORECASE
            )
            sport_match = re.search(r"Sport:\s*(\w+)", response_text, re.IGNORECASE)

            category = (
                category_match.group(1).strip().lower() if category_match else None
            )
            sport = sport_match.group(1).strip().lower() if sport_match else None
            if sport == "n/a":
                sport = None

            if not category:
                logger.error(f"Failed to parse category from response: {response_text}")
                return MessageCategory.UNRELATED, None

            normalized_category = self._normalize_category(category)
            if normalized_category is None:
                logger.warning(
                    f"Unknown category '{category}' received. Defaulting to UNRELATED."
                )
                return MessageCategory.UNRELATED, None

            if normalized_category != MessageCategory.UNRELATED and not sport:
                logger.warning(
                    f"Sport not specified for sports-related category '{category}' in message: {message}"
                )

            logger.info(
                f"Classified message '{message}' as: {normalized_category.value}, sport: {sport}"
            )
            return normalized_category, sport

        except Exception as e:
            logger.error(f"Error classifying message '{message}': {str(e)}")
            return MessageCategory.UNRELATED, None

    def _normalize_category(self, category: str) -> Optional[MessageCategory]:
        category = category.lower()
        for enum_cat in MessageCategory:
            if enum_cat.value == category:
                return enum_cat
        if "match" in category or "specific" in category or "request" in category:
            return MessageCategory.MATCH_SPECIFIC_REQUEST
        elif "betting" in category or "suggestion" in category or "update" in category:
            return MessageCategory.BETTING_SUGGESTION_OR_UPDATE
        elif "general" in category or "information" in category:
            return MessageCategory.GENERAL_SPORT_INFORMATION
        elif "unrelated" in category:
            return MessageCategory.UNRELATED
        return None
