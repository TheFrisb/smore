import logging
from typing import List, Union, Optional

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate

from core.models import SportLeague

logger = logging.getLogger(__name__)


class LeagueExtractor:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = PromptTemplate(
            input_variables=["history", "message", "sport"],
            template="""
                You are an AI assistant tasked with extracting the formal names of sports leagues and their associated countries from a conversation. The sport being discussed is {sport}. Given the conversation history and the current message, identify the league and country being referred to in the current message.

                **Instructions:**
                - Respond with the formal league name and the country name, separated by a comma (e.g., "Premier League, England"), if both are mentioned or if only a country is mentioned (in which case, assume it refers to the top league in that country).
                - If only a league is mentioned without a country, provide just the league name.
                - Handle common abbreviations and slang names for leagues and map them to their formal names (e.g., "EPL" → "Premier League", "Spanish league" → "La Liga").
                - If no league or country is referred to, respond with "No league found."
                - Consider the conversation history to resolve any ambiguities.

                Conversation History:
                {history}

                Current Message: {message}

                Examples:
                - Current Message: "Give me betting picks for the Premier League"
                  Response: "Premier League"
                - Current Message: "What about the EPL?"
                  Response: "Premier League"
                - Current Message: "Any updates on La Liga?"
                  Response: "La Liga"
                - Current Message: "Tell me about the Spanish league"
                  Response: "La Liga, Spain"
                - Current Message: "How's the Premier League in Scotland?"
                  Response: "Scottish Premiership, Scotland"
                - Current Message: "What's happening in the NBA?"
                  Response: "NBA"
                - Current Message: "Any good bets for the English league?"
                  Response: "Premier League, England"
                - Current Message: "Bets for Germany"
                  Response: "Bundesliga, Germany"
                - Current Message: "Any good bets today?"
                  Response: "No league found."
            """,
        )
        self.chain = self.prompt | self.llm

    def extract(
            self,
            message: str,
            history: List[Union[HumanMessage, AIMessage]],
            sport: Optional[str] = None,
    ) -> Optional[SportLeague]:
        try:
            # Format the conversation history
            history_text = "\n".join(
                [
                    f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
                    for msg in history
                ]
            )
            sport_str = sport if sport else "not specified"
            logger.info(
                f"Extracting league with message: '{message}', sport: '{sport_str}', history: '{history_text}'"
            )

            # Invoke the LLM with the prompt
            response = self.chain.invoke(
                {"history": history_text, "message": message, "sport": sport_str}
            )
            response_text = response.content.strip()

            # Handle case where no league is found
            if response_text == "No league found.":
                logger.info("No league found in the message.")
                return None

            # Parse the response
            parts = [part.strip() for part in response_text.split(",")]
            if len(parts) == 1:
                league_name = parts[0]
                country = None
            elif len(parts) == 2:
                league_name = parts[0]
                country = parts[1]
            else:
                logger.warning(f"Unexpected response format: {response_text}")
                return None

            # Query the database for the league
            if country:
                league_obj = SportLeague.objects.filter(
                    name__iexact=league_name, country__name__iexact=country
                ).first()
            else:
                league_obj = SportLeague.objects.filter(name__iexact=league_name).first()

            if not league_obj:
                logger.warning(f"No league found for name: {league_name}, country: {country}")
                return None

            logger.info(f"Extracted league: {league_obj.name}, country: {league_obj.country}")
            return league_obj

        except Exception as e:
            logger.error(f"Error extracting league: {e}")
            return None
