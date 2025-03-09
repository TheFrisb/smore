import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MessageCategory(Enum):
    SPORT_MATCH_ANALYSIS = "sport_match_analysis"
    SPORT_MATCH_PREDICTION = "sport_match_prediction"
    GENERAL_SPORT_INFORMATION = "general_sport_information"
    UNRELATED = "unrelated"


class MessageClassifier:
    def __init__(self, llm, classification_prompt):
        self.llm = llm
        self.prompt = classification_prompt
        self.chain = self.prompt | self.llm

    def classify(self, message: str) -> MessageCategory:
        try:
            response = self.chain.invoke({"message": message})
            raw_category = response.content.strip().lower()
            logger.info(f"Classified message as: {raw_category}")
            return self._normalize_category(raw_category)
        except Exception as e:
            logger.error(f"Error classifying message: {e}")
            return MessageCategory.UNRELATED

    def _normalize_category(self, category: str) -> MessageCategory:
        for enum_cat in MessageCategory:
            if enum_cat.value == category:
                return enum_cat
        if "analysis" in category:
            return MessageCategory.SPORT_MATCH_ANALYSIS
        elif "prediction" in category:
            return MessageCategory.SPORT_MATCH_PREDICTION
        elif "general" in category or "information" in category:
            return MessageCategory.GENERAL_SPORT_INFORMATION
        return MessageCategory.UNRELATED
