"""
This module synchronizes events using a cost function approach.
It calculates a cost matrix based on event types and phases,
and then finds the optimal sequence for each event.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""
from typing import Any, List, Tuple

import floodlight
import floodlight.io.kinexon as fliok
import numpy as np
import pandas as pd

import variables.data_variables as dv
from help_functions.pos_data_approach import (find_key_position,
                                              get_pid_from_name,
                                              get_pos_filepath, normalize)


def sigmoid(
    x: Any,
    a: float = 0.0,
    b: float = 1.0,
    c: float = 1.0,
    d: float = 1.0,
    e: float = 0.0,
) -> Any:
    """Function to calculate the sigmoid function.
    The base is a + b / (1 + c * np.exp(d * -(x - e))).
    When only x is given, the
    function will return the sigmoid function with the default
    values of a=0, b=1, c=1,
    d=1, e=0 resulting in the sigmoid function 1 / (1 + exp(-x)).

    Args:
        x (float | np.ndarray): input value(s) for the sigmoid
        function
        a (float, optional): The first parameter. Defaults to 0.
        b (float, optional): The second parameter. Defaults to 1.
        c (float, optional): The third parameter. Defaults to 1.
        d (float, optional): The fourth parameter. Defaults to 1.
        e (float, optional): The fifth parameter. Defaults to 0.

    Returns:
        float | np.ndarray: The sigmoid function value(s) for the
        input value(s) x
    """
    in_exp = np.clip(d * -(x - e), a_min=-700, a_max=700)
    return a + (b / (1 + c * np.exp(in_exp)))


def calculate_cost_matrix(events: pd.DataFrame,
                          sequences: List[Tuple[int, int, int]],
                          match_id: int,
                          ) -> np.ndarray:
    """
    Calculates the cost matrix for event synchronization.

    Args:
        events: DataFrame with event data
        sequences: List of sequence tuples (start, end, phase)

    Returns:
        np.ndarray: Cost matrix
    """
    cost_matrix = np.full((len(events), len(sequences)), np.inf)

    # Reduzierte maximale Zeitdifferenz, da Events vor der Zeit stattfinden
    MAX_TIME_DIFF = 1000

    for i, event in enumerate(events.values):
        print("event nummer: ", i)
        event_time = event[24]
        event_type = event[0]
        competitor = event[25]
        links, pos_data, ball_data, pid = prepare_position_cost(
            match_id, event)
        # event_frequency = calculate_event_frequency(events, event_type, i)

        for j, (start, end, phase) in enumerate(sequences):
            time_diff = event_time - end

            if (start > event_time) or (time_diff < -MAX_TIME_DIFF):
                continue

            # temporal_cost = calculate_temporal_cost(time_diff)
            phase_cost = calculate_phase_cost(phase, competitor, event_type)
            position_cost = get_distance_ball_player_cost(
                links, pos_data, ball_data, pid, start, end)
            if (position_cost is None) or (phase_cost is None):
                continue

            total_cost = (
                0.5 * position_cost +
                0.5 * phase_cost
            )

            cost_matrix[i, j] = total_cost

    return cost_matrix


def prepare_position_cost(match_id: int,
                          event: pd.Series) -> tuple[Any, Any, Any, Any]:
    """
    Calculates the position cost for an event.

    Args:
        match_id: The match ID
        events: The events DataFrame

    Returns:
        links: Dictionary with player IDs and their assignments
        t_event: Time of the event
        pos_data: XY-object with the player positions
        ball_data: XY-object with the ball positions
        pid: The player ID (name)

    """
    filepath_data = get_pos_filepath(match_id)
    pos_data = fliok.read_position_data_csv(filepath_data)
    pid_dict, _, _, _ = fliok.get_meta_data(
        filepath_data)
    xids = fliok.create_links_from_meta_data(pid_dict, identifier="name")
    ball_num = find_key_position(pid_dict, "Ball")

    if event[0] in ["score_change", "shot_saved", "shot_off_target",
                    "shot_blocked", "technical_rule_fault",
                    "seven_m_awarded", "steal", "technical_ball_fault"]:
        if not isinstance(event[8], type(None)):
            pos_num = find_key_position(pid_dict, event[10])
            for i in xids.items():
                if i[0] == event[10]:
                    links = i[1]
                    if isinstance(links, tuple):
                        links = links[0]
                    return (links,
                            pos_data[pos_num],
                            pos_data[ball_num],
                            event[8])
        elif not isinstance(event[14], type(None)):
            pos_num = find_key_position(pid_dict, event[10])
            for i in xids.items():
                if i[0] == event[10]:
                    links = i[1]
                    if isinstance(links, tuple):
                        links = links[0]
                    return (links,
                            pos_data[pos_num],
                            pos_data[ball_num],
                            event[14]["name"])

    return None, None, None, None


def calculate_phase_cost(phase: int, competitor: dv.Team,
                         event_type: str) -> float:
    """
    Calculates the phase-based costs for an event.

    Args:
        phase: Current phase
        competitor: Team (HOME/AWAY)
        event_type: Type of the event

    Returns:
        float: Phase costs
    """
    critical_events = {
        "score_change": 1.0,
        "shot_saved": 0.9,
        "shot_blocked": 0.9,
        "seven_m_awarded": 0.8,
        "shot_off_target": 0.7,
        "technical_ball_fault": 0.7,
        "technical_rule_fault": 0.7,
        "steal": 0.7,
    }
    non_critical_events = {
        "yellow_card": 0.1,
        "suspension": 0.1,
        "substitution": 0.1,
        "suspension_over": 0.2,
    }
    inactive_events = {
        "seven_m_missed": 0.7,
        "timeout_over": 0.9,
        "period_start": 0.7,
        "period_end": 0.7,
        "match_started": 0.7,
        "match_ended": 0.7,
        "break_start": 0.7,
        "period_score": 0.5,
    }
    if event_type in inactive_events:
        if phase == 0:
            return 0.0
        else:
            return inactive_events[event_type]
    if event_type == "timeout":
        if phase == 0:
            return 0.0
        elif ((phase in (1, 3) and competitor == dv.Team.A) or
                (phase in (2, 4) and competitor == dv.Team.B)):
            return 0.0
        else:
            return 1.0

    # Determine base costs based on event type
    base_cost = critical_events.get(event_type,
                                    non_critical_events.get(
                                        event_type,
                                        inactive_events.get(
                                            event_type, 0.5)))

    if event_type in critical_events:
        # Check phase compatibility
        if ((phase in (1, 3) and competitor == dv.Team.A) or
                (phase in (2, 4) and competitor == dv.Team.B)):
            return 0.0  # Correct phase

        return base_cost  # Wrong phase
    return base_cost


def sync_events_cost_function(events: pd.DataFrame,
                              sequences: List[Tuple[int, int, int]],
                              match_id: int) -> pd.DataFrame:
    """
    Synchronizes events using a cost function.

    Args:
        events: DataFrame with event data
        sequences: List of sequence tuples

    Returns:
        pd.DataFrame: Synchronized events
    """
    cost_matrix = calculate_cost_matrix(events, sequences, match_id)

    # Find optimal assignment for each event
    for i, _ in enumerate(events.values):
        event_costs = cost_matrix[i]
        best_sequence_idx = np.argmin(event_costs)

        if event_costs[best_sequence_idx] < np.inf:
            start, end, _ = sequences[best_sequence_idx]
            events.iloc[i, 24] = start + (end - start) // 2

    return events


def get_distance_ball_player_cost(links: Any,
                                  pos_data: floodlight.core.xy.XY,
                                  ball_data: floodlight.core.xy.XY,
                                  pid: str, start: int, end: int) -> Any:
    """
    Calculates the distance between the ball and the player.

    Args:
        links: Dictionary with player IDs and their assignments
        pos_data: XY-object with the player positions
        ball_num: Number of the ball
        pos_num: Number of the player
        t_event: Time of the event

    Returns:
        float: Distance between the ball and the player
    """
    if (pid or links or pos_data or ball_data) is None:
        return None
    # Normalize player ID and get numerical ID
    pid = normalize(pid)
    pid_num = get_pid_from_name(pid, links)

    # Get player positions data
    player_data = pos_data.player(pid_num)

    # Combine the two ball data sets
    ball_data_1 = ball_data.player(0)
    ball_data_2 = ball_data.player(1)
    # Check if ball data arrays have different shapes
    if ball_data_1.shape != ball_data_2.shape:
        # If first ball data array is empty, use second ball data array
        if ball_data_1.size == 0:
            ball_positions = ball_data_2
        # If second ball data array is empty, keep first ball data array
        elif ball_data_2.size == 0:
            ball_positions = ball_data_1
    else:
        ball_positions = np.where(np.isnan(ball_data_1), ball_data_2,
                                  ball_data_1)

    # Slice der Daten für den Zeitbereich zwischen start und end
    ball_positions = ball_positions[start:end+1]
    player_data = player_data[start:end+1]

    distance = np.hypot(
        # x-Koordinaten (erste Stelle)
        ball_positions[:, 0] - player_data[:, 0],
        # y-Koordinaten (zweite Stelle)
        ball_positions[:, 1] - player_data[:, 1]
    )

    # Betrachte nur die letzten 10% des Zeitintervalls
    window_size = max(1, int(0.1 * len(distance)))
    end_window = distance[-window_size:]

    # Kleinste Distanz im Endfenster
    min_distance = np.nanmin(end_window)
    return sigmoid(min_distance, d=5, e=2.5)
