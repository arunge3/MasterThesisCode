"""
This module synchronizes events using a cost function approach.
It calculates a cost matrix based on event types and phases,
and then finds the optimal sequence for each event.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""
from typing import Any

import floodlight.io.kinexon as fliok
import numpy as np
import pandas as pd

import position_helpers
import template_start
import variables.data_variables as dv
from help_functions.pos_data_approach import (find_key_position,
                                              get_pid_from_name,
                                              get_pos_filepath, normalize)

# def get_distance_ball_event_cost(tracking_data, event):
#     distance = np.hypot(
#         tracking_data["ball_x"].values - event["start_x"],
#         tracking_data["ball_y"].values - event["start_y"]
#         )
#     return sigmoid(distance, d=5, e=6)


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


def get_distance_ball_player_cost(ball_data: np.ndarray,
                                  player_data: np.ndarray
                                  ) -> np.ndarray:
    """
    Calculates the distance between the ball and the player.
    Args:
        ball_data: The ball data
        player_data: The player data

    Returns:
        np.ndarray: The distance between the ball and the player
    """
    if player_data.all() is None:
        return np.inf
    # ball_data = np.where(np.isnan(ball_data), np.inf, ball_data)
    # player_data = np.where(np.isnan(player_data), np.inf,
    # player_data)

    distance = np.hypot(
        # x-Koordinaten (erste Stelle)
        ball_data[:, 0] - player_data[:, 0],
        # y-Koordinaten (zweite Stelle)
        ball_data[:, 1] - player_data[:, 1]
    )
    return sigmoid(distance, d=5, e=2.5)


def get_ball_acceleration_cost(ball_acceleration: np.ndarray
                               ) -> np.ndarray:
    """
    Calculates the acceleration cost for the ball.
    Args:
        ball_acceleration: The acceleration of the ball

    Returns:
        np.ndarray: The acceleration cost for the ball
    """
    return sigmoid(-ball_acceleration, d=0.2, e=-25.0)


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


def prepare_position_cost(pos_data: Any,
                          pid_dict: Any,
                          xids: Any,
                          event: pd.Series
                          ) -> tuple[Any, Any, Any]:
    """
    Calculates the position cost for an event.

    Args:
        pos_data: The position data
        pid_dict: The player ID dictionary
        xids: The player ID dictionary
        event: The event

    Returns:
        links: Dictionary with player IDs and their assignments
        pos_data: XY-object with the player positions
        pid: The player ID (name)

    """

    if event[0] in ["score_change", "shot_saved", "shot_off_target",
                    "shot_blocked", "technical_rule_fault",
                    "seven_m_awarded", "steal", "technical_ball_fault"]:
        if not isinstance(event[8], type(None)):
            pos_num = find_key_position(pid_dict, event[10])
            for i in xids.items():
                if template_start.fuzzy_match_team_name(
                        event[10], i[0]):
                    links = i[1]
                    if isinstance(links, tuple):
                        links = links[0]
                    return (links,
                            pos_data[pos_num],
                            event[8])
        elif not isinstance(event[14], type(None)):
            pos_num = find_key_position(pid_dict, event[10])
            for i in xids.items():
                if template_start.fuzzy_match_team_name(
                        event[10], i[0]):
                    links = i[1]
                    if isinstance(links, tuple):
                        links = links[0]

                    return (links,
                            pos_data[pos_num],
                            event[14]["name"])

    return None, None, None


def prepare(match_id: int) -> tuple[Any, Any, Any, Any]:
    """
    Prepares the data for the cost function.
    Args:
        match_id: The match ID

    Returns:
        tuple: The position data, the ball data, the player
        ID dictionary, and the player ID dictionary
    """
    filepath_data = get_pos_filepath(match_id)
    pos_data = fliok.read_position_data_csv(filepath_data)

    pid_dict, _, _, _ = fliok.get_meta_data(
        filepath_data)
    xids = fliok.create_links_from_meta_data(pid_dict, identifier="name")
    ball_num = find_key_position(pid_dict, "Ball")
    return pos_data, pos_data[ball_num], pid_dict, xids


def main(match_id: int, events: Any) -> Any:
    """
    Main function to prepare the data for the cost function.
    Args:
        match_id: The match ID
        events: The events

    Returns:
        Any: The events with the tracking indices

    """
    pos_data, ball_data, pid_dict, xids = prepare(match_id)
    ball_data, ball_acceleration = position_helpers.prepare_ball_data(
        ball_data)
    for idx, event in enumerate(events.values):
        links, player_data, pid = prepare_position_cost(
            pos_data, pid_dict, xids, event)
        if player_data is not None:
            pid = normalize(pid)
            pid_num = get_pid_from_name(pid, links)

            # Get player positions data
            player_data = player_data.player(pid_num)
            pos_cost = get_distance_ball_player_cost(ball_data, player_data)
            acc_cost = get_ball_acceleration_cost(ball_acceleration)
            # phase_cost = calculate_phase_cost(event[0], event[1], event[2])
            total_cost = pos_cost + acc_cost  # + phase_cost
            total_cost = inf_values(
                total_cost, event[24], player_data, ball_data)
            # Ersetze NaN-Werte durch inf, damit sie nicht als Minimum
            # gewählt werden
            total_cost = np.where(np.isnan(total_cost), np.inf, total_cost)
            tracking_idx = total_cost.argmin()
            if tracking_idx != 0:
                lowest_cost = (
                    total_cost / 2
                ).min()
            else:
                lowest_cost = 0

            if lowest_cost <= 0.5 and tracking_idx != 0:
                events.iloc[idx, 24] = tracking_idx
                print(lowest_cost)
                print(tracking_idx)
    return events


def inf_values(total_cost: Any,
               time: Any,
               player_data: Any,
               ball_data: Any) -> Any:
    """
    Inf values for the cost function.
    Args:
        total_cost: The total cost
        time: The time
        player_data: The player data
        ball_data: The ball data

    Returns:
        Any: The total cost
    """
    if time is None or time <= 0:
        return total_cost

    # Ensure time is within bounds
    data_length = len(player_data)
    if time >= data_length:
        time = data_length - 1

    # Set future values to infinity
    total_cost[time:] = np.inf

    none_idx = 0
    max_time = max(0, time - 500)  # Ensure max_time is not negative

    # Check for None values in the window
    for t in range(time - 1, max_time - 1, -1):
        if t >= data_length:
            continue
        if player_data[t].any() is None or ball_data[t].any() is None:
            none_idx += 1

    if none_idx >= 499:
        for t in range(max_time - 1, -1, -1):
            if t >= data_length:
                continue
            if player_data[t].any() is None or ball_data[t].any() is None:
                none_idx += 1
            else:
                break

    if none_idx > 10:
        print(f"Game was interrupted for {none_idx} frames")
        # Ensure max_time is not negative
        max_time = max(0, max_time - none_idx)

    # Set past values to infinity
    for t in range(max_time - 1, -1, -1):
        if t < data_length:
            total_cost[t] = np.inf

    return total_cost
