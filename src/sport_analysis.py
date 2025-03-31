from typing import Any, Counter, Union

import variables.data_variables as dv
from template_start import run_template_matching


def calculate_next_phase(events: Any) -> dict[Any, Any]:
    """
    Calculates the next phase for each event based on the sequences.
    Counts how often each event type is followed by specific phases.

    Returns:
        Dictionary with structure:
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


def calculate_goal_success_rate_per_phase(events: Any
                                          ) -> (dict[str,
                                                     dict[str, object]]):
    """
    Calculates the goal success rate per phase.
    """
    (position_events_home, counter_events_home,
     neutral_events_home, position_events_away,
     counter_events_away, neutral_events_away
     ) = evaluate_phase_events(events)

    # Initialize a dictionary to store goal counts and success rates
    goal_stats = {
        'home': {
            'position': {'goals': 0, 'total': len(position_events_home)},
            'counter': {'goals': 0, 'total': len(counter_events_home)},
            'neutral': {'goals': 0, 'total': len(neutral_events_home)}
        },
        'away': {
            'position': {'goals': 0, 'total': len(position_events_away)},
            'counter': {'goals': 0, 'total': len(counter_events_away)},
            'neutral': {'goals': 0, 'total': len(neutral_events_away)}
        }
    }

    # Count goals for each phase and team
    for event in position_events_home:
        if event[0] in ["score_change"]:
            goal_stats['home']['position']['goals'] += 1

    for event in position_events_away:
        if event[0] in ["score_change"]:
            goal_stats['away']['position']['goals'] += 1

    for event in counter_events_home:
        if event[0] in ["score_change"]:
            goal_stats['home']['counter']['goals'] += 1

    for event in counter_events_away:
        if event[0] in ["score_change"]:
            goal_stats['away']['counter']['goals'] += 1

    for event in neutral_events_home:
        if event[0] in ["score_change"]:
            goal_stats['home']['neutral']['goals'] += 1

    for event in neutral_events_away:
        if event[0] in ["score_change"]:
            goal_stats['away']['neutral']['goals'] += 1

    # Calculate success rates
    pos_suc_rate_home = (goal_stats['home']['position']['goals'] /
                         goal_stats['home']['position']['total'] if
                         goal_stats['home']['position']['total'] > 0 else 0)
    pos_suc_rate_away = (goal_stats['away']['position']['goals'] /
                         goal_stats['away']['position']['total'] if
                         goal_stats['away']['position']['total'] > 0 else 0)
    counter_suc_rate_home = (goal_stats['home']['counter']['goals'] /
                             goal_stats['home']['counter']['total'] if
                             goal_stats['home']['counter']['total'] > 0 else 0)
    counter_suc_rate_away = (goal_stats['away']['counter']['goals'] /
                             goal_stats['away']['counter']['total'] if
                             goal_stats['away']['counter']['total'] > 0 else 0)
    neutral_suc_rate_home = (goal_stats['home']['neutral']['goals'] /
                             goal_stats['home']['neutral']['total'] if
                             goal_stats['home']['neutral']['total'] > 0 else 0)
    neutral_suc_rate_away = (goal_stats['away']['neutral']['goals'] /
                             goal_stats['away']['neutral']['total'] if
                             goal_stats['away']['neutral']['total'] > 0 else 0)
    # Create a dictionary to store all the analysis results
    analysis_results = {
        'Goal_success_rate_per_phase': {
            'goal_stats': goal_stats,
            'success_rates': {
                'home': {
                    'position': pos_suc_rate_home,
                    'counter': counter_suc_rate_home,
                    'neutral': neutral_suc_rate_home
                },
                'away': {
                    'position': pos_suc_rate_away,
                    'counter': counter_suc_rate_away,
                    'neutral': neutral_suc_rate_away
                }
            },
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
                          ) -> (tuple[list[Any], list[Any], list[Any],
                                      list[Any], list[Any], list[Any]]):
    """
    Analyzes events and defensive formations at specific times
    in the game.
    Args:
        events (pd.DataFrame): DataFrame with event data

    Returns:
        tuple: Tuple with statistics on events and formations
        per phase
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
            if event[28] in [1]:
                position_events_home.append(event)
            elif event[28] in [3]:
                counter_events_home.append(event)
            elif event[28] in [2]:
                position_events_away.append(event)
            elif event[28] in [4]:
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
    Analyzes the number of players on the field at specific times
    in the game.
    Args:
        events (pd.DataFrame): DataFrame with event data

    Returns:
        dict: Dictionary with statistics on events and formations
        per phase
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
        'Goal_Rate in Unter- und Überzahl': {
            'home': {
                'goal_rate_full': goal_rate_full_home,
                'goal_rate_uberzahl': goal_rate_uberzahl_home,
                'goal_rate_outnumbered': goal_rate_outnumbered_home,
                'goal_rate_both_outnumbered': goal_rate_both_outnumbered_home
            },
            'away': {
                'goal_rate_full': goal_rate_full_away,
                'goal_rate_uberzahl': goal_rate_uberzahl_away,
                'goal_rate_outnumbered': goal_rate_outnumbered_away,
                'goal_rate_both_outnumbered': goal_rate_both_outnumbered_away
            }
        }
    }
    return analysis_results


def analyze_events_and_formations(events: Any, match_id: int
                                  ) -> dict[Any, Any]:
    """
    Analyzes events and defensive formations at specific
    times in the game.

    Args:
        events (pd.DataFrame): DataFrame with event data
        match_id (int): ID of the match to be analyzed

    Returns:
        dict: Dictionary with statistics on events and
        formations per phase
    """
    # Template Matching ausführen
    phase_results = run_template_matching(match_id)

    # Ergebnisdictionary initialisieren
    analysis_results: dict[Any, Any]
    analysis_results = {
        phase: {'events': [], 'formations': []} for phase in range(5)
    }
    for event in events.values:
        event_time = event[24]
        event_type = event[0]

        current_phase = None
        for phase_info in phase_results:

            if phase_info['start'] <= event_time <= phase_info['end']:
                current_phase = phase_info['phase_type']
                formation = phase_info['formation']
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
                             'score_change']:
                    total_shots += 1
                    if event == 'score_change':
                        successful_goals += 1

            goal_success_rate = (successful_goals /
                                 total_shots * 100) if total_shots > 0 else 0
            formation_stats[formation] = {
                'total_shots': total_shots,
                'goals': successful_goals,
                'goal_success_rate': goal_success_rate
            }

        analysis_results[phase] = {
            'event_statistics': dict(events_count),
            'formation_statistics': dict(formations_count),
            'formation_goal_rates': formation_stats
        }

    return {
        'goal_success_rate_per_formation': analysis_results
    }


def create_combined_statistics(events: Any, match_id: int
                               ) -> dict[Any, Any]:
    """
    Creates a combined analysis of all statistics,
    merging the results from all analyses
    Args:
        events (pd.DataFrame): DataFrame with event data
        match_id (int): ID of the match to be analyzed

    Returns:
        dict: Dictionary with combined statistics
    """
    # Gather all individual statistics
    formation_stats = analyze_events_and_formations(events, match_id)
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
                            dv.Opponent.HOME,
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
                            dv.Opponent.HOME,
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
                            dv.Opponent.HOME,
                            is_equal_strength=True)
                    },
                    'positional_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[28] == 3)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[28] == 3 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            dv.Opponent.HOME,
                            phase_type=3),
                        'against_formations': _calculate_opponent_formations(
                            events,
                            dv.Opponent.HOME,
                            phase_type=3)
                    },
                    'counter_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[28] == 1)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.HOME and
                            e[28] == 1 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            dv.Opponent.HOME,
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
                            dv.Opponent.AWAY,
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
                            dv.Opponent.AWAY,
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
                            dv.Opponent.AWAY,
                            is_equal_strength=True)
                    },
                    'positional_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[28] == 4)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[28] == 4 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            dv.Opponent.AWAY,
                            phase_type=4),
                        'against_formations':
                            _calculate_opponent_formations(
                            events,
                            dv.Opponent.AWAY,
                            phase_type=4)
                    },
                    'counter_attacks': {
                        'total_attempts': len([e for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[28] == 2)]),
                        'goals': sum(1 for e in events.values if (
                            e[21] ==
                            dv.Opponent.AWAY and
                            e[28] == 2 and
                            e[0] == 'score_change')),
                        'next_phase_distribution':
                            _calculate_next_phases_for_situation(
                            events,
                            dv.Opponent.AWAY,
                            phase_type=2)
                    }
                }
            },
            'phase_transition_analysis': {
                'successful_attacks': {
                    'total': sum(1 for e in events.values if (
                        e[0] == 'score_change')),
                    'by_previous_phase':
                        (next_phase_stats['Next_Phase_Statistics']
                         ['score_change']['next_phases'])
                },
                'failed_attacks': {
                    'total': sum(1 for e in events.values if (
                        e[0] in ['shot_saved', 'shot_blocked',
                                 'shot_off_target'])),
                    'leading_to_phase': _calculate_failed_attack_transitions(
                        events)
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


def _calculate_next_phases_for_situation(events: Any, team: Any,
                                         is_outnumbered: bool = False,
                                         is_power_play: bool = False,
                                         is_equal_strength: bool = False,
                                         phase_type: Union[int, None] = None
                                         ) -> dict[int, int]:
    """
    Helper function to calculate next phase distribution for
    specific situations
    Args:
        events: The event data
        team: The team (HOME/AWAY) whose attacks we're analyzing
        is_outnumbered: Whether to filter for outnumbered attacks
        is_power_play: Whether to filter for power play attacks
        is_equal_strength: Whether to filter for equal strength attacks
        phase_type: The phase type to analyze (3 for home positional,
        4 for away positional)
    """
    phase_counts = {1: 0, 2: 0, 3: 0, 4: 0}

    for event in events.values:
        if event[21] != team:
            continue

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


def _calculate_failed_attack_transitions(events: Any) -> dict[int, int]:
    """Helper function to analyze where failed attacks lead to
    Args:
        events: The event data

    Returns:
        Dictionary with transition counts for each phase
    """
    transition_counts = {1: 0, 2: 0, 3: 0, 4: 0}

    for event in events.values:
        if event[0] in ['shot_saved', 'shot_blocked',
                        'shot_off_target']:
            if event[29] in [1, 2, 3, 4]:
                transition_counts[event[29]] += 1

    return transition_counts


def _calculate_opponent_formations(events: Any, team: Any,
                                   phase_type: int
                                   ) -> dict[str, dict[str, int]]:
    """
    Calculate statistics for each opponent formation
    encountered during positional attacks.

    Args:
        events: The event data
        team: The team (HOME/AWAY) whose attacks we're analyzing
        phase_type: The phase type to analyze (3 for home
        positional, 4 for away positional)

    Returns:
        Dictionary with formation statistics:
        {
            'formation_name': {
                'total_attempts': int,
                'goals': int,
                'failed_attempts': int  # shots saved,
                blocked, or off target
            }
        }
    """
    formation_stats = {}

    for event in events.values:

        # Check if it's the correct team and phase
        if event[21] != team or event[28] != phase_type:
            continue

        # Get the opponent's formation
        if event[25] == dv.Team.NONE:
            formation = "none"
        elif event[25] == dv.Team.A:
            formation = "Team A"
        elif event[25] == dv.Team.B:
            formation = "Team B"
        else:
            formation = "unknown"

        # Initialize formation stats if not exists
        if formation not in formation_stats:
            formation_stats[formation] = {
                'total_attempts': 0,
                'goals': 0,
                'failed_attempts': 0
            }

        # Update statistics
        formation_stats[formation]['total_attempts'] += 1

        if event[0] == 'score_change':
            formation_stats[formation]['goals'] += 1
        elif event[0] in ['shot_saved', 'shot_blocked', 'shot_off_target']:
            formation_stats[formation]['failed_attempts'] += 1

    return formation_stats
