import logging
from typing import List, Tuple

from django.db.models import Q

from core.models import SportTeam, SportMatch

logger = logging.getLogger(__name__)


class TeamExtractor:
    def __init__(self, llm, team_extraction_prompt):
        self.llm = llm
        self.prompt = team_extraction_prompt
        self.chain = self.prompt | self.llm

    def extract(self, message: str) -> Tuple[List[SportTeam], List[SportMatch]]:
        try:
            response = self.chain.invoke({"message": message})
            extracted_names = [
                name.strip() for name in response.content.split(",") if name.strip()
            ]
            logger.info(f"Extracted team names: {extracted_names}")

            if not extracted_names:
                logger.info("No team names extracted.")
                return [], []

            matched_teams = []
            for name in extracted_names:
                team = SportTeam.objects.filter(name__iexact=name).first()
                if team:
                    matched_teams.append(team)
                else:
                    logger.warning(
                        f"No case-insensitive match found for team name: {name}"
                    )

            if not matched_teams:
                logger.info("No matching teams found.")
                return [], []

            matches = SportMatch.objects.filter(
                Q(home_team__in=matched_teams) | Q(away_team__in=matched_teams)
            ).order_by("-kickoff_datetime")

            return matched_teams, list(matches)

        except Exception as e:
            logger.error(f"Error extracting teams and matches: {e}")
            return [], []
