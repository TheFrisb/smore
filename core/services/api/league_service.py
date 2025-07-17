from time import sleep

from core.models import SportLeague, ApiSportModel, SportTeam, SportLeagueTeam
from core.services.api.in_progress.BaseApiFootballService import BaseApiFootballService
from core.services.api.team_standings import TeamStandingsService


class LeagueService(BaseApiFootballService):
    def update_league_season_year(self):
        endpoint = "leagues"
        response = self.get_endpoint(endpoint=endpoint, query_params=None)

        body = response.get("response", [])
        for item in body:
            league_external_id = item.get("league", {}).get("id")
            seasons = item.get("seasons", [])

            active_season_with_coverage = self._find_active_season_with_coverage(seasons)
            if not active_season_with_coverage:
                self.log.info(f"No active season with coverage found for league {league_external_id}.")
                continue

            self._update_league(
                league_external_id=league_external_id,
                year=active_season_with_coverage.get("year"),
                coverage=active_season_with_coverage.get("coverage")
            )

    def map_teams_to_leagues(self):
        endpoint = "teams"
        sport_leagues = SportLeague.objects.filter(type=ApiSportModel.SportType.SOCCER,
                                                   current_season_year__isnull=False)

        for league in sport_leagues:
            # sleep to avoid hitting API rate limits
            sleep(0.5)
            query_params = {
                "league": league.external_id,
                "season": league.current_season_year
            }
            response = self.get_endpoint(endpoint=endpoint, query_params=query_params)
            body = response.get("response", [])

            if not body:
                self.log.info(f"No teams found for league {league.external_id} in season {league.current_season_year}.")
                continue

            for item in body:
                team_external_id = item.get("team", {}).get("id")
                if not team_external_id:
                    self.log.warning(f"Team ID not found for league {league.external_id}. Skipping.")
                    continue

                sport_team = SportTeam.objects.filter(
                    external_id=team_external_id,
                    type=ApiSportModel.SportType.SOCCER
                ).first()

                if not sport_team:
                    self.log.warning(f"SportTeam not found for external ID {team_external_id}. Skipping.")
                    continue

                try:
                    SportLeagueTeam.objects.create(
                        league=league,
                        team=sport_team,
                        season=league.current_season_year
                    )
                    self.log.info(f"Mapped team {team_external_id} to league {league.external_id}.")
                except Exception as e:
                    self.log.error(f"Error mapping team {team_external_id} to league {league.external_id}: {e}")

    def fetch_and_update_team_standings(self):
        sport_leagues = SportLeague.objects.filter(type=ApiSportModel.SportType.SOCCER,
                                                   current_season_year__isnull=False)

        team_standing_service = TeamStandingsService()
        for league in sport_leagues:
            team_standing_service.update_team_standings(league.external_id, league.current_season_year)

    def _find_active_season_with_coverage(self, seasons) -> dict:
        if not seasons:
            return {}

        for season in seasons:
            is_current_season = season.get("current", False)
            if not is_current_season:
                continue

            year = season.get("year")
            coverage = season.get("coverage")

            return {
                "year": year,
                "coverage": coverage
            }

        return {}

    def _update_league(self, league_external_id: int, year: str, coverage: dict):
        SportLeague.objects.filter(external_id=league_external_id, type=ApiSportModel.SportType.SOCCER).update(
            current_season_year=year,
            api_coverage_data=coverage
        )

        self.log.info(f"Updated league {league_external_id} with year: {year}")
