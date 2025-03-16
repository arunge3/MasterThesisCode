from typing import Any, Counter

import variables.data_variables as dv
from template_start import run_template_matching


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
      Analyzes events and defensive formations at specific times
    in the game.

    Args:
        events (pd.DataFrame): DataFrame with event data
        sequences (pd.DataFrame): DataFrame with sequence data
        match_id (int): ID of the match to be analyzed

    Returns:
        dict: Dictionary with statistics on events and formations
        per phase
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

    # Zusammenfassung erstellen
    for phase in analysis_results:
        events_count = Counter(analysis_results[phase]['events'])
        formations_count = Counter(analysis_results[phase]['formations'])
        analysis_results[phase] = {
            'event_statistics': dict(events_count),
            'formation_statistics': dict(formations_count)
        }
    total_shots = 0
    successful_goals = 0
    for phase in analysis_results:
        for event, count in analysis_results[phase]['event_statistics'
                                                    ].items():
            if event in ['shot_blocked', 'shot_saved', 'shot_off_target',
                         'score_change']:
                total_shots += count
                if event == 'score_change':
                    successful_goals += count

        if total_shots > 0:
            goal_success_rate = (successful_goals / total_shots) * 100
        else:
            goal_success_rate = 0

        analysis_results[phase]['goal_success_rate'] = goal_success_rate

    # Add a higher level structure with goal_success_rate_per_formation
    return {
        'goal_success_rate_per_formation': analysis_results,

    }
