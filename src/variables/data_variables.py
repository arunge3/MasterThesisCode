
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
        ML_RB (str): Represents a machine learning approach with
        rule-based.
        COST_FUNCTION (str): Represents a cost function based approach.
        ML_CORRECTION (str): Represents a machine learning approach with
                            correction.
    """

    RULE_BASED = "Rule-based Approach"
    BASELINE = "Baseline"
    NONE = "No Calcuation"
    ML_BASED = "Machine Learning Approach"
    ML_RB = "Machine Learning Approach with Rule-based"
    ML_CORRECTION = "ML Approach with Correction"
    COST_BASED = "Cost-based Approach"


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
    HOME = "home"
    AWAY = "away"
    NONE = "none"


class Team(Enum):
    """
    Enum class representing the opponent in a game.
    Attributes:
        HOME (str): Represents the home team.
        AWAY (str): Represents the away team.
        NONE (str): Represents no opponent.
    """
    A = "first team after alphabetical order"
    B = "second team after alphabetical order"
    NONE = "none"
