"""
This module provides comprehensive analysis functions for handball
match statistics. It includes functions for calculating phase
transitions, goal success rates, player counts, and formation
analysis. The module processes event data to generate detailed
match statistics and insights.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""

from typing import Any, Counter, Union

import variables.data_variables as dv
from preprocessing.template_matching.template_start import \
    run_template_matching


def calculate_next_phase(events: Any) -> dict[Any, Any]:
    """
    Calculates the next phase for each event based on the sequences.
    Counts how often each event type is followed by specific phases.

    Args:
        events (pd.DataFrame): DataFrame containing event data with
        columns:
            - event_type: Type of the event
            - next_phase: The phase that follows the event

    Returns:
        dict: Dictionary with structure:
            {
                'Next_Phase_Statistics': {
                    'event_type': {
                        'total': total_count,
                        'next_phases': {
                            1: count_phase_1,
                            2: count_phase_2,
                            3: count_phase_3,
                            4: count_phase_4
                        }
                    }
                }
            }
    """
    stats: dict[str, dict[str, Union[int, dict[int, int]]]] = {}

    for event in events.values:
        event_type = str(event[0])  # Ensure event_type is a string
        next_phase = event[29]

        # Skip if event type is not interesting or next phase is None
        if event_type not in ["score_change", "shot_saved", "shot_off_target",
                              "shot_blocked", "technical_rule_fault",
                              "seven_m_awarded", "steal",
                              "technical_ball_fault"]:
            continue

        # Initialize dict for new event type
        if event_type not in stats:
            stats[event_type] = {
                'total': 0,
                'next_phases': {1: 0, 2: 0, 3: 0, 4: 0}
            }

        # Safely access and increment total count
        total = stats[event_type]['total']
        if isinstance(total, int):
            stats[event_type]['total'] = total + 1

        # Count next phase if it exists
        if next_phase is not None and next_phase in [1, 2, 3, 4]:
            next_phases = stats[event_type]['next_phases']
            if isinstance(next_phases, dict) and next_phase in next_phases:
                next_phases[next_phase] += 1

    return {'Next_Phase_Statistics': stats}


def calculate_goal_success_rate_per_phase(
    events: Any
) -> dict[str, dict[str, dict[str, dict[Any, Any]]]]:
    """
    Calculates two success rates per phase:
    1. Goal rate: score_change / (total_events - seven_m_awarded)
    2. Successful attack rate: (score_change + seven_m_awarded) / total_events

    Args:
        events (pd.DataFrame): DataFrame containing event data with columns:
            - event_type: Type of the event (e.g., 'score_change',
            'seven_m_awarded')
            - phase_type: Type of phase (position, counter, neutral)
            - team: Team identifier (home/away)

    Returns:
        dict: Dictionary with structure:
            {
                'Goal_success_rate_per_phase': {
                    'event_stats': {
                        'home/away': {
                            'position/counter/neutral': {
                                'score_change': int,
                                'seven_m_awarded': int,
                                'total': int
                            }
                        }
                    },
                    'success_rates': {
                        'home/away': {
                            'position/counter/neutral': {
                                'goal_rate': float,
                                'successful_attack_rate': float
                            }
                        }
                    }
                }
            }
    """
    (position_events_home, counter_events_home,
     neutral_events_home, position_events_away,
     counter_events_away, neutral_events_away) = evaluate_phase_events(events)

    # Initialize a dictionary to store counts
    stats = {
        'home': {
            'position': {'score_change': 0, 'seven_m_awarded': 0,
                         'total': len(position_events_home)},
            'counter': {'score_change': 0, 'seven_m_awarded': 0,
                        'total': len(counter_events_home)},
            'neutral': {'score_change': 0, 'seven_m_awarded': 0,
                        'total': len(neutral_events_home)}
        },
        'away': {
            'position': {'score_change': 0, 'seven_m_awarded': 0,
                         'total': len(position_events_away)},
            'counter': {'score_change': 0, 'seven_m_awarded': 0,
                        'total': len(counter_events_away)},
            'neutral': {'score_change': 0, 'seven_m_awarded': 0,
                        'total': len(neutral_events_away)}
        }
    }

    # Count events for each phase and team
    for team, phase_types in [
        ('home', [(position_events_home, 'position'),
                  (counter_events_home, 'counter'),
                  (neutral_events_home, 'neutral')]),
        ('away', [(position_events_away, 'position'),
                  (counter_events_away, 'counter'),
                  (neutral_events_away, 'neutral')])
    ]:
        for events_list, phase_type in phase_types:
            for event in events_list:
                if event[0] == "score_change":
                    stats[team][phase_type]['score_change'] += 1
                elif event[0] == "seven_m_awarded":
                    stats[team][phase_type]['seven_m_awarded'] += 1

    # Calculate both rates for each team and phase
    success_rates: dict[str, dict[Any, Any]] = {
        'home': {},
        'away': {}
    }

    for team in ['home', 'away']:
        for phase_type in ['position', 'counter', 'neutral']:
            phase_stats = stats[team][phase_type]
            total_events = phase_stats['total']
            events_without_7m = total_events - phase_stats['seven_m_awarded']

            # Calculate goal rate (excluding 7m from denominator)
            goal_rate = (phase_stats['score_change'] / events_without_7m
                         if events_without_7m > 0 else 0)

            # Calculate successful attack rate (including
            # both goals and 7m awards)
            successful_attack_rate = ((phase_stats['score_change'] +
                                       phase_stats['seven_m_awarded'])
                                      / total_events if total_events > 0
                                      else 0)

            success_rates[team][phase_type] = {
                'goal_rate': goal_rate,
                'successful_attack_rate': successful_attack_rate
            }

    # Create final analysis results
    analysis_results = {
        'Goal_success_rate_per_phase': {
            'event_stats': stats,
            'success_rates': success_rates,
            'event_counts': {
                'home': {
                    'position': len(position_events_home),
                    'counter': len(counter_events_home),
                    'neutral': len(neutral_events_home)
                },
                'away': {
                    'position': len(position_events_away),
                    'counter': len(counter_events_away),
                    'neutral': len(neutral_events_away)
                }
            }
        }
    }

    return analysis_results


def evaluate_phase_events(events: Any
                          ) -> tuple[list[Any], list[Any], list[Any],
                                     list[Any], list[Any], list[Any]]:
    """
    Analyzes events and categorizes them into different phase types
    for both teams.

    Args:
        events (pd.DataFrame): DataFrame containing event data with
        columns:
            - event_type: Type of the event
            - phase_type: Type of phase (1-4)
            - team: Team identifier (home/away)
            - opponent: Opponent team identifier

    Returns:
        tuple: Contains six lists of events:
            - position_events_home: Position attack events for home team
            - counter_events_home: Counter attack events for home team
            - neutral_events_home: Neutral events for home team
            - position_events_away: Position attack events for away team
            - counter_events_away: Counter attack events for away team
            - neutral_events_away: Neutral events for away team
    """
    position_events_home = []
    counter_events_home = []
    neutral_events_home = []
    position_events_away = []
    counter_events_away = []
    neutral_events_away = []
    for event in events.values:
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            if event[28] in [3]:
                position_events_home.append(event)
            elif event[28] in [1]:
                counter_events_home.append(event)
            elif event[28] in [4]:
                position_events_away.append(event)
            elif event[28] in [2]:
                counter_events_away.append(event)
            elif event[28] in [0]:
                if event[21] is not None:
                    if event[21] == dv.Opponent.AWAY:
                        neutral_events_away.append(event)
                    else:
                        neutral_events_home.append(event)
    return (position_events_home, counter_events_home, neutral_events_home,
            position_events_away, counter_events_away, neutral_events_away)


def calculate_player_count_per_phase(events: Any) -> dict[Any, Any]:
    """
    Analyzes the number of players on the field during different phases
    and calculates goal rates for various player count situations.

    Args:
        events (pd.DataFrame): DataFrame containing event data with columns:
            - event_type: Type of the event
            - team: Team identifier (home/away)
            - home_players: Number of home team players
            - away_players: Number of away team players

    Returns:
        dict: Dictionary containing goal rates for different player
        count situations:
            {
                'Goal_Rate power_play and outnumbered attacks': {
                    'home': {
                        'goal_rate_full': float,
                        'goal_rate_power_play': float,
                        'goal_rate_outnumbered': float,
                        'goal_rate_both_outnumbered': float
                    },
                    'away': {
                        'goal_rate_full': float,
                        'goal_rate_power_play': float,
                        'goal_rate_outnumbered': float,
                        'goal_rate_both_outnumbered': float
                    }
                }
            }
    """
    home_full_events = []
    away_full_events = []
    home_uberzahl_events = []
    home_outnumbered_events_defense = []
    home_both_outnumbered_events = []
    away_uberzahl_events = []
    away_outnumbered_events_defense = []
    away_both_outnumbered_events = []
    for event in events.values:
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            if event[26] is not None and event[27] is not None:
                if event[21] == dv.Opponent.HOME:
                    if (event[26] >= 7 and event[27] >= 7):
                        home_full_events.append(event)
                    elif event[26] >= 7 and event[27] < 7:
                        home_uberzahl_events.append(event)
                    elif event[26] < 7 and event[27] >= 7:
                        home_outnumbered_events_defense.append(event)
                    elif event[26] < 7 and event[27] < 7:
                        home_both_outnumbered_events.append(event)
                elif event[21] == dv.Opponent.AWAY:
                    if (event[26] >= 7 and event[27] >= 7):
                        away_full_events.append(event)
                    elif event[26] >= 7 and event[27] < 7:
                        away_uberzahl_events.append(event)
                    elif event[26] < 7 and event[27] >= 7:
                        away_outnumbered_events_defense.append(event)
                    elif event[26] < 7 and event[27] < 7:
                        away_both_outnumbered_events.append(event)

    home_full_score = 0
    away_full_score = 0
    home_uberzahl_score = 0
    away_uberzahl_score = 0
    home_outnumbered_score = 0
    away_outnumbered_score = 0
    home_both_outnumbered_score = 0
    away_both_outnumbered_score = 0
    for event in home_full_events:
        if event[0] in ["score_change"]:
            home_full_score += 1
    for event in away_full_events:
        if event[0] in ["score_change"]:
            away_full_score += 1
    for event in home_uberzahl_events:
        if event[0] in ["score_change"]:
            home_uberzahl_score += 1
    for event in away_uberzahl_events:
        if event[0] in ["score_change"]:
            away_uberzahl_score += 1
    for event in home_outnumbered_events_defense:
        if event[0] in ["score_change"]:
            home_outnumbered_score += 1
    for event in away_outnumbered_events_defense:
        if event[0] in ["score_change"]:
            away_outnumbered_score += 1
    for event in home_both_outnumbered_events:
        if event[0] in ["score_change"]:
            home_both_outnumbered_score += 1
    for event in away_both_outnumbered_events:
        if event[0] in ["score_change"]:
            away_both_outnumbered_score += 1
    if len(home_full_events) > 0:
        goal_rate_full_home = home_full_score / len(home_full_events)
    else:
        goal_rate_full_home = 0
    if len(home_uberzahl_events) > 0:
        goal_rate_uberzahl_home = home_uberzahl_score / \
            len(home_uberzahl_events)
    else:
        goal_rate_uberzahl_home = 0
    if len(home_outnumbered_events_defense) > 0:
        goal_rate_outnumbered_home = home_outnumbered_score / \
            len(home_outnumbered_events_defense)
    else:
        goal_rate_outnumbered_home = 0
    if len(home_both_outnumbered_events) > 0:
        goal_rate_both_outnumbered_home = home_both_outnumbered_score / \
            len(home_both_outnumbered_events)
    else:
        goal_rate_both_outnumbered_home = 0
    if len(away_full_events) > 0:
        goal_rate_full_away = away_full_score / len(away_full_events)
    else:
        goal_rate_full_away = 0
    if len(away_uberzahl_events) > 0:
        goal_rate_uberzahl_away = away_uberzahl_score / \
            len(away_uberzahl_events)
    else:
        goal_rate_uberzahl_away = 0
    if len(away_outnumbered_events_defense) > 0:
        goal_rate_outnumbered_away = away_outnumbered_score / \
            len(away_outnumbered_events_defense)
    else:
        goal_rate_outnumbered_away = 0
    if len(away_both_outnumbered_events) > 0:
        goal_rate_both_outnumbered_away = away_both_outnumbered_score / \
            len(away_both_outnumbered_events)
    else:
        goal_rate_both_outnumbered_away = 0

    analysis_results = {
        'Goal_Rate power_play and outnumbered attacks': {
            'home': {
                'goal_rate_full': goal_rate_full_home,
                'goal_rate_power_play': goal_rate_uberzahl_home,
                'goal_rate_outnumbered': goal_rate_outnumbered_home,
                'goal_rate_both_outnumbered': goal_rate_both_outnumbered_home
            },
            'away': {
                'goal_rate_full': goal_rate_full_away,
                'goal_rate_power_play': goal_rate_uberzahl_away,
                'goal_rate_outnumbered': goal_rate_outnumbered_away,
                'goal_rate_both_outnumbered': goal_rate_both_outnumbered_away
            }
        }
    }
    return analysis_results


def analyze_events_and_formations(events: Any, match_id: int
                                  ) -> tuple[dict[str, dict[Any, Any]], Any]:
    """
    Analyzes events and defensive formations during different phases of the
    game.

    Args:
        events (pd.DataFrame): DataFrame containing event data with columns:
            - event_type: Type of the event
            - time: Timestamp of the event
            - team: Team identifier (home/away)
        match_id (int): Unique identifier for the match

    Returns:
        tuple: Contains two elements:
            1. dict: Dictionary with formation analysis results:
                {
                    'attack_success_rate_per_formation': {
                        phase_number: {
                            'event_statistics': dict,
                            'formation_statistics': dict,
                            'formation_attack_success_rates': dict
                        }
                    }
                }
            2. pd.DataFrame: Updated events DataFrame with formation
            information
    """
    # Template Matching ausführen
    phase_results = run_template_matching(match_id)

    # Ergebnisdictionary initialisieren
    analysis_results: dict[Any, Any]
    analysis_results = {
        phase: {'events': [], 'formations': []} for phase in range(5)
    }
    if 'opponent_formation' not in events.columns:
        events['opponent_formation'] = None

    for idx, event in events.iterrows():
        event_time = event[24]
        event_type = event[0]

        current_phase = None
        for phase_info in phase_results:

            if phase_info['start'] <= event_time <= phase_info['end']:
                current_phase = phase_info['phase_type']
                formation = phase_info['formation']
                events.loc[idx, 'opponent_formation'] = formation
                break

        if current_phase is not None:
            analysis_results[current_phase]['events'].append(event_type)
            analysis_results[current_phase]['formations'].append(formation)

    # Modify the summary creation section
    for phase in analysis_results:
        events_count = Counter(analysis_results[phase]['events'])
        formations_count = Counter(analysis_results[phase]['formations'])

        # Create formation-specific statistics
        formation_stats = {}
        events_by_formation: dict[str, list[str]] = {}

        # Group events by formation
        for event_type, formation in zip(analysis_results[phase]['events'],
                                         analysis_results[phase]['formations']
                                         ):
            if event_type in ['shot_blocked', 'shot_saved', 'shot_off_target',
                              'score_change', 'seven_m_awarded', 'steal',
                              'technical_ball_fault', 'technical_rule_fault']:
                formation_str = str(formation)  # Ensure formation is a string
                if formation_str not in events_by_formation:
                    events_by_formation[formation_str] = []
                events_by_formation[formation_str].append(str(event_type))

        # Calculate success rate for each formation
        for formation, formation_events in events_by_formation.items():
            total_shots = 0
            successful_goals = 0

            for event in formation_events:
                if event in ['shot_blocked', 'shot_saved', 'shot_off_target',
                             'score_change', 'seven_m_awarded', 'steal',
                             'technical_ball_fault', 'technical_rule_fault']:
                    total_shots += 1
                    if event in ['score_change', 'seven_m_awarded']:
                        successful_goals += 1

            goal_success_rate = (successful_goals /
                                 total_shots * 100) if total_shots > 0 else 0
            formation_stats[formation] = {
                'total_shots': total_shots,
                'goals': successful_goals,
                'attack_success_rate': goal_success_rate
            }

        analysis_results[phase] = {
            'event_statistics': dict(events_count),
            'formation_statistics': dict(formations_count),
            'formation_attack_success_rates': formation_stats
        }

    return {
        'attack_success_rate_per_formation': analysis_results
    }, events


def create_combined_statistics(events: Any, match_id: int
                               ) -> dict[Any, Any]:
    """
    Creates a comprehensive analysis combining all match statistics
    including player situations, phase transitions, and formation analysis.

    Args:
        events (pd.DataFrame): DataFrame containing event data with columns:
            - event_type: Type of the event
            - time: Timestamp of the event
            - team: Team identifier (home/away)
            - home_players: Number of home team players
            - away_players: Number of away team players
        match_id (int): Unique identifier for the match

    Returns:
        dict: Dictionary containing combined match statistics:
            {
                'Combined_Match_Statistics': {
                    'player_situation_analysis': {
                        'home/away': {
                            'outnumbered_attacks': {...},
                            'power_play_attacks': {...},
                            'equal_strength_attacks': {...},
                            'positional_attacks': {...},
                            'counter_attacks': {...}
                        }
                    },
                    'phase_transition_analysis': {...},
                    'original_statistics': {
                        'formations': {...},
                        'phases': {...},
                        'player_counts': {...},
                        'next_phases': {...}
                    }
                }
            }
    """
    # Gather all individual statistics
    formation_stats, events = analyze_events_and_formations(events, match_id)
    phase_stats = calculate_goal_success_rate_per_phase(events)
    player_count_stats = calculate_player_count_per_phase(events)
    next_phase_stats = calculate_next_phase(events)
    # all_events = ["score_change", "shot_saved", "shot_off_target",
    #               "shot_blocked", "technical_rule_fault",
    #   "seven_m_awarded", "steal", "technical_ball_fault"]
    # Create combined insights
    combined_stats = {}
    combined_stats = {
        'Combined_Match_Statistics': {
            'player_situation_analysis': {
                'home': {
                    'outnumbered_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[26] is not None and
                            e[26] < 7)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[26] is not None and
                            e[26] < 7 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            is_outnumbered=True)
                    },
                    'power_play_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[27] is not None and
                            e[27] < 7)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[27] is not None and
                            e[27] < 7 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            is_power_play=True)
                    },
                    'equal_strength_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[26] is not None and
                            e[27] is not None and
                            e[26] >= 7 and
                            e[27] >= 7)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[26] is not None and
                            e[27] is not None and
                            e[26] >= 7 and
                            e[27] >= 7 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            is_equal_strength=True)
                    },
                    'positional_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[28] == 3)]),
                        'goals': sum(1 for e in events.values if (
                            e[28] == 3 and
                            e[0] in ['score_change', 'seven_m_awarded'])),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            phase_type=3),
                        'against_formations': _calculate_opponent_formations(
                            events,
                            phase_type=3)
                    },
                    'counter_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[28] == 1)]),
                        'goals': sum(1 for e in events.values if (
                            e[28] == 1 and
                            e[0] in ['score_change', 'seven_m_awarded'])),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            phase_type=1)
                    }
                },
                'away': {
                    'outnumbered_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[26] is not None and
                            e[26] < 7)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[26] is not None and
                            e[26] < 7 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            is_outnumbered=True)
                    },
                    'power_play_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[27] is not None and
                            e[27] < 7)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[27] is not None and
                            e[27] < 7 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            is_power_play=True)
                    },
                    'equal_strength_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[26] is not None and
                            e[27] is not None and
                            e[26] >= 7 and
                            e[27] >= 7)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[26] is not None and
                            e[27] is not None and
                            e[26] >= 7 and
                            e[27] >= 7 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            is_equal_strength=True)
                    },
                    'positional_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[28] == 4)]),
                        'goals': sum(1 for e in events.values if (
                            e[28] == 4 and
                            e[0] in ['score_change', 'seven_m_awarded'])),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            phase_type=4),
                        'against_formations':
                            _calculate_opponent_formations(
                            events,
                            phase_type=4)
                    },
                    'counter_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[28] == 2)]),
                        'goals': sum(1 for e in events.values if (
                            e[28] == 2 and
                            e[0] in ['score_change', 'seven_m_awarded'])),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            phase_type=2)
                    }
                }
            },
            'phase_transition_analysis': {
                'successful_attacks': {
                    'total': sum(1 for e in events.values if (
                        e[0] in ['score_change', 'seven_m_awarded'])),
                },
                'failed_attacks': {
                    'total': sum(1 for e in events.values if (
                        e[0] in ['shot_saved', 'shot_blocked',
                                 'shot_off_target', 'technical_rule_fault',
                                 'technical_ball_fault', 'steal'])),
                    'leading_to_phase': {
                        phase: sum(
                            (next_phase_stats['Next_Phase_Statistics']
                             [event]['next_phases']).get(
                                str(phase), 0)
                            for event in (next_phase_stats
                                          ['Next_Phase_Statistics'])
                            if event not in ['score_change', 'seven_m_awarded']
                        )
                        for phase in ['1', '2', '3', '4']
                    }
                }
            },
            'original_statistics': {
                'formations': formation_stats,
                'phases': phase_stats,
                'player_counts': player_count_stats,
                'next_phases': next_phase_stats
            }
        }
    }
    print(type(combined_stats))

    return combined_stats


def _calculate_next_phases_for_situation(events: Any,
                                         is_outnumbered: bool = False,
                                         is_power_play: bool = False,
                                         is_equal_strength: bool = False,
                                         phase_type: Union[int, None] = None
                                         ) -> dict[int, int]:
    """
    Helper function to calculate the distribution of next phases for specific
    game situations.

    Args:
        events (pd.DataFrame): DataFrame containing event data
        is_outnumbered (bool, optional): Whether to analyze outnumbered
        situations
        is_power_play (bool, optional): Whether to analyze power play
        situations
        is_equal_strength (bool, optional): Whether to analyze equal
        strength situations
        phase_type (int, optional): Specific phase type to analyze (1-4)

    Returns:
        dict: Dictionary mapping phase numbers to their occurrence counts:
            {
                1: count_phase_1,
                2: count_phase_2,
                3: count_phase_3,
                4: count_phase_4
            }
    """
    phase_counts = {1: 0, 2: 0, 3: 0, 4: 0}

    for event in events.values:

        # Skip if conditions don't match
        if is_outnumbered and (event[26] is None or event[26] >= 7):
            continue
        if is_power_play and (event[27] is None or event[27] >= 7):
            continue
        if is_equal_strength and (event[26] is None or event[27] is None or
                                  event[26] < 7 or event[27] < 7):
            continue
        if phase_type is not None and event[28] != phase_type:
            continue

        if event[29] in [1, 2, 3, 4]:
            phase_counts[event[29]] += 1

    return phase_counts


def _calculate_opponent_formations(events: Any,
                                   phase_type: int
                                   ) -> dict[str, dict[str, int]]:
    """
    Calculates statistics for each opponent formation encountered during
    positional attacks.

    Args:
        events (pd.DataFrame): DataFrame containing event data with columns:
            - event_type: Type of the event
            - phase_type: Type of phase (1-4)
            - formation: Opponent's formation type
        phase_type (int): The phase type to analyze (3 for home positional,
        4 for away positional)

    Returns:
        dict: Dictionary containing formation statistics:
            {
                'formation_name': {
                    'total_attempts': int,
                    'goals': int,
                    'failed_attempts': int
                }
            }
        where formation_name can be '60', '51', '321', or 'unknown'
    """
    formation_stats = {}

    for event in events.values:

        # Check if it's the correct team and phase
        if event[28] != phase_type:
            continue

        # Get the opponent's formation
        if event[30] == "60":
            formation = "60"
        elif event[30] == "51":
            formation = "51"
        elif event[30] == "321":
            formation = "321"
        else:
            formation = "unknown"

        # Initialize formation stats if not exists
        if formation not in formation_stats:
            formation_stats[formation] = {
                'total_attempts': 0,
                'goals': 0,
                'failed_attempts': 0
            }

        if event[0] in ['score_change', 'seven_m_awarded']:
            formation_stats[formation]['goals'] += 1
            formation_stats[formation]['total_attempts'] += 1
        elif event[0] in ['shot_saved', 'shot_blocked', 'shot_off_target',
                          'technical_rule_fault', 'technical_ball_fault',
                          'steal']:
            formation_stats[formation]['failed_attempts'] += 1
            formation_stats[formation]['total_attempts'] += 1

    return formation_stats


def _calculate_formation_success_rates(formation_stats:
                                       dict[str, dict[str, int]]
                                       ) -> dict[str, float]:
    """
    Calculates success rates for each formation type based on the provided
    statistics.
    Success rate is defined as the percentage of attempts that resulted
    in goals.

    Args:
        formation_stats (dict): Dictionary containing formation statistics:
            {
                'formation_name': {
                    'total_attempts': int,
                    'goals': int,
                    'failed_attempts': int
                }
            }

    Returns:
        dict: Dictionary containing success rates for each formation:
            {
                'formation_name': float  # success rate as a percentage
            }
        where formation_name can be '60', '51', '321', or 'unknown'
    """
    goal_rates = {}
    for formation, stats in formation_stats.items():
        total_attempts = stats['total_attempts']
        goals = stats['goals']
        goal_rate = (goals / total_attempts) * 100 if total_attempts > 0 else 0
        goal_rates[formation] = goal_rate
    return goal_rates
