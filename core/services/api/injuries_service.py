from typing import Optional, Dict, List

from ai_assistant.v2.tools.api.match_injuries import TeamWithInjuryOutputModel, InjuryOutputModel
from ai_assistant.v2.types import PlayerOutputModel, SportTeamOutputModel
from core.models import SportMatch, Player, ApiSportModel
from core.services.api.in_progress.BaseApiFootballService import BaseApiFootballService


class InjuriesService(BaseApiFootballService):
    def fetch_injuries_for_match(self, match: SportMatch):
        endpoint = "injuries"
        query_params = {
            "fixture": match.external_id,
        }

        response = self.get_endpoint(endpoint=endpoint, query_params=query_params)
        body = response.get("response", [])

        if not body:
            self.log.info(f"No injuries found for match {match.external_id}.")

        return body

    def load_injuries_for_tool(self, match: SportMatch, response_body: list[dict]) -> Optional[
        list[TeamWithInjuryOutputModel]]:
        if not response_body:
            return None

        team_injuries: Dict[int, List[InjuryOutputModel]] = {}

        for item in response_body:
            self.log.info(f"Loading injuries for match {match.external_id}.")
            try:
                player = Player.objects.get(external_id=item["player"]["id"], type=ApiSportModel.SportType.TEMP_FIX)
                injury_type = item["player"]["reason"]
                will_play_status = item["player"]["type"]
                team_external_id = item["team"]["id"]

                if team_external_id not in team_injuries:
                    team_injuries[team_external_id] = []

                injury_model = InjuryOutputModel(
                    player=PlayerOutputModel.from_django(player),
                    injury_type=injury_type,
                    will_play_status=will_play_status
                )

                team_injuries[team_external_id].append(injury_model)
            except Exception as e:
                self.log.error(f"Error loading injury data for match {match.external_id}: {e}")

        home_team = match.home_team
        away_team = match.away_team

        home_team_model = SportTeamOutputModel.model_validate(home_team)
        away_team_model = SportTeamOutputModel.model_validate(away_team)

        home_injuries = team_injuries.get(home_team.external_id, [])
        away_injuries = team_injuries.get(away_team.external_id, [])

        home_team_with_injuries = TeamWithInjuryOutputModel(
            team=home_team_model,
            injuries=home_injuries
        )

        away_team_with_injuries = TeamWithInjuryOutputModel(
            team=away_team_model,
            injuries=away_injuries
        )

        return [home_team_with_injuries, away_team_with_injuries] if home_injuries or away_injuries else None
