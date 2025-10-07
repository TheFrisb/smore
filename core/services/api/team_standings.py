from time import sleep

from core.models import SportLeague, SportLeagueTeam, SportTeam, TeamStanding
from core.services.api.in_progress.BaseApiFootballService import BaseApiFootballService


class TeamStandingsService(BaseApiFootballService):
    def update_team_standings(self, league_external_id: int, season_year: int):
        endpoint = "standings"
        query_params = {"league": league_external_id, "season": season_year}

        response = self.get_endpoint(endpoint=endpoint, query_params=query_params)
        body = response.get("response", [])

        if not body:
            self.log.info(
                f"No standings data found for {league_external_id} in {season_year}"
            )
            return

        standings = body[0].get("league", {}).get("standings", [])

        if not standings:
            self.log.info(
                f"No standings data found for {league_external_id} in {season_year}, even though the response was not empty"
            )
            return

        for data in standings[0]:
            team_external_id = data.get("team", {}).get("id")
            sleep(0.5)

            try:
                sport_league_team = SportLeagueTeam.objects.filter(
                    team__external_id=team_external_id,
                    league__external_id=league_external_id,
                    season=season_year,
                ).first()

                if not sport_league_team:
                    SportLeagueTeam.objects.create(
                        league=SportLeague.objects.get(external_id=league_external_id),
                        team=SportTeam.objects.get(external_id=team_external_id),
                    )

                team_standing, created = TeamStanding.objects.get_or_create(
                    league_team=sport_league_team,
                    defaults={
                        "data": data,
                    },
                )

                if not created:
                    team_standing.data = data
                    team_standing.save()
                    self.log.info(
                        f"Updated existing TeamStanding for team {team_external_id} in league {league_external_id} for season {season_year}"
                    )
                else:
                    self.log.info(
                        f"Created new TeamStanding for team {team_external_id} in league {league_external_id} for season {season_year}"
                    )
            except Exception as e:
                self.log.error(
                    f"Error processing team {team_external_id} in league {league_external_id} for season {season_year}: {e}"
                )
                continue
