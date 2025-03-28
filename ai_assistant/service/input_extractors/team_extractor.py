import logging
from typing import List, Union, Optional

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate

from core.models import SportTeam

logger = logging.getLogger(__name__)


class TeamExtractor:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = PromptTemplate(
            input_variables=["history", "message", "sport"],
            template="""
                    You are an AI assistant tasked with extracting the full names of sports teams from a conversation. The sport being discussed is {sport}. Given the conversation history and the current message, identify the teams being referred to in the current message. If the message refers to a match, provide the full names of the teams involved in that match.

                    **Instructions:**
                    - Respond **only** with the full team names as a comma-separated list (e.g., "Real Madrid, Barcelona").
                    - Note that a team name can also be a country name (e.g., "Spain", "Netherlands", "Denmark").
                    - Be aware that team names may be misspelled or abbreviated in the user's messages. Use the AI's responses to infer the correct team names when necessary.
                    - Do not include any additional text, explanations, or sentences in your response.
                    - If the message refers to "this match", "the match", "last match", or similar vague phrases, assume it refers to the last match mentioned in the conversation history.
                    - If no teams are referred to, respond with "No teams found."

                    Conversation History:
                    {history}

                    Current Message: {message}

                    Examples:
                    - History: "User: Tell me about Spain vs Netherlands. AI: Here’s the analysis for Spain vs Netherlands... User: Now Portugal vs Denmark. AI: Here’s the analysis for Portugal vs Denmark..."
                      Current Message: "Can you give me other betting predictions for this match?"
                      Sport: soccer
                      Response: "Portugal, Denmark"
                    - History: "User: Give me a prediction for England vs Lativa. AI: Here’s the prediction for England vs Latvia..."
                      Current Message: "Give me other predictions for that match"
                      Sport: soccer
                      Response: "England, Latvia"
                    - History: "User: Give me detailed match prediction of Gibraltar vs Lativa. AI: Here’s the prediction for Gibraltar vs Latvia..."
                      Current Message: "Give me other bets to play for that match"
                      Sport: soccer
                      Response: "Gibraltar, Latvia"
                    - History: None
                      Current Message: "real vs barca"
                      Sport: soccer
                      Response: "Real Madrid, Barcelona"
                    """,
        )
        self.chain = self.prompt | self.llm

    def extract(
        self,
        message: str,
        history: List[Union[HumanMessage, AIMessage]],
        sport: Optional[str] = None,
    ) -> List[SportTeam]:
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
                f"Extracting teams with message: '{message}', sport name: {sport_str} and history: '{history_text}'"
            )

            # Invoke the LLM with the prompt
            response = self.chain.invoke(
                {"history": history_text, "message": message, "sport": sport}
            )
            extracted_names = [
                name.strip() for name in response.content.split(",") if name.strip()
            ]
            logger.info(f"Extracted team names: {extracted_names}")

            # Handle the case where no teams are found
            if extracted_names and extracted_names != ["No teams found"]:
                matched_teams = self._match_teams(extracted_names)
                if matched_teams:
                    return matched_teams

            logger.info("No team names extracted.")
            return []
        except Exception as e:
            logger.error(f"Error extracting teams: {e}")
            return []

    def _match_teams(self, extracted_names: List[str]) -> List[SportTeam]:
        if extracted_names == ["No teams found"]:
            return []
        matched_teams = []
        for name in extracted_names:
            team = SportTeam.objects.filter(name__iexact=name).first()
            if team:
                matched_teams.append(team)
            else:
                logger.warning(f"No case-insensitive match found for team name: {name}")
        return matched_teams
