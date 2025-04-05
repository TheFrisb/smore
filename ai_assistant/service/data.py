from enum import Enum

from pydantic import BaseModel

from accounts.models import User


class SportClassification(Enum):
    """
    Enum for classifying the sport types
    """

    SOCCER = "SOCCER"


class PromptType(Enum):
    """
    Enum for classifying the prompt types
    """

    # When the user wants to predict a single match. E.g: "Give me a prediction for Manchester United vs Chelsea"
    SINGLE_MATCH_PREDICTION = "SINGLE_MATCH_PREDICTION"

    # When the user wants to predict multiple matches. E.g: "Give me a prediction for Manchester United vs Chelsea and Liverpool vs Arsenal"
    MULTI_MATCH_PREDICTION = "MULTI_MATCH_PREDICTION"

    # When the user wants to predict a single league. E.g: "Give me a prediction for the Premier League"
    SINGLE_LEAGUE_PREDICTION = "SINGLE_LEAGUE_PREDICTION"

    # When the user wants to predict multiple leagues. E.g: "Give me a prediction for the Premier League and La Liga"
    MULTI_LEAGUE_PREDICTION = "MULTI_LEAGUE_PREDICTION"

    # When the user wants the model to suggest a random match to predict. E.g: "Give me a match prediction"
    SINGLE_RANDOM_MATCH_PREDICTION = "RANDOM_SPORT_PREDICTION"

    # When the user wants the model to suggest multiple random matches to predict. E.g: "Give me some match predictions"
    MULTI_RANDOM_MATCH_PREDICTION = "RANDOM_SPORT_PREDICTION"

    # When the user asks for sport betting ticket builder. E.g: "Give me a betting ticket for the Premier League"
    SPORT_TICKET_BUILDER = "SPORT_TICKET_BUILDER"

    # Any other question that doesn't fit the above categories.
    GENERAL_SPORT_QUESTION = "GENERAL_SPORT_QUESTION"

    # When the prompt is not sport related
    NOT_SPORT_RELATED = "NOT_SPORT_RELATED"


class PromptClassifierModel(BaseModel):
    """
    Class for classifying the prompt
    """

    prompt_type: PromptType
    team_names: list[str]
    league_names: list[str]
    suggested_dates: list[str]


class PromptContext:
    """
    Class for classifying the prompt context
    """

    def __init__(self, user: User, prompt: str):
        self.user = user
        self.prompt = prompt
        self.history = []
        self.prompt_type = None
        self.team_names = []
        self.league_names = []
        self.suggested_dates = []
        self.team_objs = []
        self.league_objs = []
        self.matches_context = []
        self.response = None
        self.can_proceed = True

    def __repr__(self):
        return (
            f"<PromptContext user={self.user} prompt={self.prompt} "
            f"prompt_type={self.prompt_type} team_names={self.team_names} "
            f"league_names={self.league_names} suggested_dates={self.suggested_dates} "
            f"response={self.response} can_proceed={self.can_proceed}>"
        )
