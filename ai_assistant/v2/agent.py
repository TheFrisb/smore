from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

from ai_assistant.v2.models import openai_o3_model
from ai_assistant.v2.tools.leagues import get_league_info
from ai_assistant.v2.tools.matches import get_matches_by_league, get_matches_by_team, get_matches_by_team_list, \
    get_match_insights_by_external_id
from ai_assistant.v2.tools.teams import get_team_info, get_team_infos_by_league
from backend import settings

tools = [TavilySearch(tavily_api_key=settings.TAVILY_API_KEY),
         get_team_info,
         get_team_infos_by_league,
         get_league_info,
         get_matches_by_league,
         get_matches_by_team,
         get_matches_by_team_list,
         get_match_insights_by_external_id
         ]

prompt = """
You are an expert sport AI Assistant working for SMORE, a professional sports research company known for accurate predictions and smart betting strategies.
Your task is to assist users with sports-related queries, provide insights, analytics, predictions, sport tickets and betting strategies.

Do not answer questions that are not related to sports or betting.
"""

agent_executor = create_react_agent(model=openai_o3_model, tools=tools, prompt=prompt)
