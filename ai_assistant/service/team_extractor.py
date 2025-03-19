import logging
from typing import List, Tuple, Union

from django.db.models import Q
from langchain_core.messages import HumanMessage, AIMessage

from core.models import SportTeam, SportMatch

logger = logging.getLogger(__name__)


class TeamExtractor:
    def __init__(self, llm, team_extraction_prompt):
        self.llm = llm
        self.prompt = team_extraction_prompt
        self.chain = self.prompt | self.llm

    def extract(
            self, message: str, history: List[Union[HumanMessage, AIMessage]]
    ) -> Tuple[List[SportTeam], List[SportMatch]]:
        try:
            logger.debug(f"Extracting teams from current message: '{message}'")
            response = self.chain.invoke({"message": message})
            extracted_names = [
                name.strip() for name in response.content.split(",") if name.strip()
            ]
            logger.info(f"Extracted team names from current message: {extracted_names}")

            if extracted_names and extracted_names != ["No teams found"]:
                matched_teams = self._match_teams(extracted_names)
                if matched_teams:
                    matches = self._get_matches(matched_teams)
                    return matched_teams, matches

            for hist_msg in reversed(history):
                if isinstance(hist_msg, HumanMessage):
                    logger.debug(
                        f"Extracting teams from history message: '{hist_msg.content}'"
                    )
                    logger.info(
                        f"Extracting teams from history message: '{hist_msg.content}'"
                    )
                    response = self.chain.invoke({"message": hist_msg.content})
                    extracted_names = [
                        name.strip()
                        for name in response.content.split(",")
                        if name.strip()
                    ]
                    logger.info(
                        f"Extracted team names from history message '{hist_msg.content}': {extracted_names}"
                    )
                    if extracted_names and extracted_names != ["No teams found"]:
                        matched_teams = self._match_teams(extracted_names)
                        if matched_teams:
                            matches = self._get_matches(matched_teams)
                            return matched_teams, matches

            logger.info("No team names extracted from message or history.")
            return [], []
        except Exception as e:
            logger.error(f"Error extracting teams and matches: {e}")
            return [], []

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

    def _get_matches(self, teams: List[SportTeam]) -> List[SportMatch]:
        matches = SportMatch.objects.filter(
            Q(home_team__in=teams) | Q(away_team__in=teams)
        ).order_by("-kickoff_datetime")[:30]
        return list(matches)
