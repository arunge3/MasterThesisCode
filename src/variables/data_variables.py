
from enum import Enum


class Approach(Enum):
    """
    Enum class representing different approaches for the synchronizatrion
    of gamephases and events.
    Attributes:
        RULE_BASED (str): Represents a rule-based approach.
        BASELINE (str): Represents a baseline approach.
        NONE (str): Represents no calculation.
        ML_BASED (str): Represents a machine learning-based approach.
    """

    RULE_BASED = "Rule-based Approach"
    BASELINE = "Baseline"
    NONE = "No Calcuation"
    ML_BASED = "Machine Learning Approach"


class Season(Enum):
    """
    Enum class representing different seasons.
    Attributes:
        SEASON_2019_2020 (str): Represents the season 2019/2020.
        SEASON_2020_2021 (str): Represents the season 2020/2021.
    """

    SEASON_2019_2020 = "19_20"
    SEASON_2020_2021 = "20_21"
    SEASON_2021_2022 = "21_22"


class Opponent(Enum):
    """
    Enum class representing the opponent in a game.
    Attributes:
        HOME (str): Represents the home team.
        AWAY (str): Represents the away team.
        NONE (str): Represents no opponent.
    """
    HOME = "Home"
    AWAY = "Away"
    NONE = "None"
