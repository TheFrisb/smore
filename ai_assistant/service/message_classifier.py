import logging
import re
from enum import Enum
from typing import List, Tuple, Optional, Union

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)


class MessageCategory(Enum):
    MATCH_SPECIFIC_REQUEST = "match_specific_request"
    GENERAL_SPORT_INFORMATION = "general_sport_information"
    UNRELATED = "unrelated"


class MessageClassifier:
    def __init__(self, llm):
        self.llm = llm
        self.system_message = SystemMessage(
            content="""
                    You are an AI assistant specializing in sports-related conversations, particularly focused on providing match analyses and betting predictions. Your task is to analyze the entire conversation history, including the current message, to determine the user's intent and the relevant sport.
                    
                    **Instructions:**
                    1. Determine if the current message or any part of the conversation history is related to sports.
                    2. If sports-related, identify the specific sport (e.g., soccer, basketball, tennis). If the current message doesn’t explicitly mention a sport but refers to prior sports-related context (e.g., teams, matches, or events), infer the sport from the history.
                    3. Classify the intent into one of these categories:
                       - match_specific_request: The user is asking for information, analysis, or predictions about a specific match between two teams. This includes messages that mention two team names or refer to a previously mentioned match.
                       - general_sport_information: The user is asking for general sports information not tied to a specific match, such as rules, player stats, team histories, etc.
                       - unrelated: The message is not sports-related, and there is no sports context in the history.
                    
                    **Rules:**
                    - If the message mentions two team names (e.g., "Barcelona vs Manchester United"), classify it as 'match_specific_request' unless the context clearly indicates otherwise (e.g., "When was Barcelona vs Manchester United founded?" would be general).
                    - If the message lacks explicit sports context but follows a sports-related conversation, infer the category and sport from the history.
                    - If neither the message nor history provides sports context, classify as 'unrelated'.
                    
                    **Examples:**
                    - Message: "Give me a bet for the Barcelona vs Manchester United match"
                      Category: match_specific_request
                      Sport: soccer
                    
                    - Message: "Tell me about the rules of soccer"
                      Category: general_sport_information
                      Sport: soccer
                    
                    - Message: "What's the weather like?"
                      Category: unrelated
                      Sport: N/A
                    
                    - History: "Barcelona vs Manchester United"
                      Current message: "Give me a detailed analysis"
                      Category: match_specific_request
                      Sport: soccer
                    
                    - Message: "When is the next Barcelona vs Manchester United match?"
                      Category: general_sport_information
                      Sport: soccer
                      
                      
                    - Message: "Who is Rafael Nadal?"
                      Category: general_sport_information
                      Sport: tennis
                    
                    **Output Format:**
                    Provide your response in the following format:
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
            logger.debug(f"Raw classification response: {response_text}")

            # Parse with regex
            category_match = re.search(
                r"Category:\s*(.+)", response_text, re.IGNORECASE
            )
            sport_match = re.search(r"Sport:\s*(.+)", response_text, re.IGNORECASE)

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

            if normalized_category != MessageCategory.UNRELATED and not sport:
                logger.warning(
                    f"Sport not specified for sports-related category '{category}' in message: {message}"
                )

            logger.info(
                f"Classified message '{message}' as: {category}, sport: {sport}"
            )
            return normalized_category, sport

        except Exception as e:
            logger.error(f"Error classifying message '{message}': {str(e)}")
            return MessageCategory.UNRELATED, None

    def _normalize_category(self, category: str) -> MessageCategory:
        category = category.lower()
        for enum_cat in MessageCategory:
            if enum_cat.value == category:
                return enum_cat
        if "match" in category or "specific" in category or "request" in category:
            return MessageCategory.MATCH_SPECIFIC_REQUEST
        elif "general" in category or "information" in category:
            return MessageCategory.GENERAL_SPORT_INFORMATION
        return MessageCategory.UNRELATED
