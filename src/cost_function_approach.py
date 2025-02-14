"""
This module synchronizes events using a cost function approach.
It calculates a cost matrix based on event types and phases,
and then finds the optimal sequence for each event.
"""
from typing import List, Tuple

import numpy as np
import pandas as pd

import variables.data_variables as dv


def calculate_cost_matrix(events: pd.DataFrame,
                          sequences: List[Tuple[int, int, int]]
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

    MAX_TIME_DIFF = 10

    for i, event in enumerate(events.values):
        event_time = event[24]  # Timestamp of the event
        event_type = event[0]   # Event-Type
        competitor = event[25]  # Team (HOME/AWAY)

        for j, (start, end, phase) in enumerate(sequences):
            time_diff = event_time - start

            if abs(time_diff) > MAX_TIME_DIFF:
                continue

            temporal_cost = calculate_temporal_cost(time_diff)

            phase_cost = calculate_phase_cost(phase, competitor, event_type)
            sequence_cost = calculate_sequential_cost(i, j, events, sequences)

            # Gesamtkosten
            total_cost = (
                0.7 * temporal_cost +
                0.2 * phase_cost +
                0.1 * sequence_cost
            )

            cost_matrix[i, j] = total_cost

    return cost_matrix


def calculate_temporal_cost(time_diff: float) -> float:
    """
    Calculates temporal costs with exponential decay.

    Args:
        time_diff: Time difference in seconds

    Returns:
        float: Temporal costs
    """
    # Preference for earlier times through asymmetric treatment
    if time_diff > 0:  # Event is later than start
        return float(1 - np.exp(-time_diff / 2))  # faster increase
    else:  # Event is earlier than start
        return float(1 - np.exp(time_diff / 4))   # slower increase


def calculate_sequential_cost(event_idx: int, seq_idx: int,
                              events: pd.DataFrame,
                              sequences: List[Tuple[int, int, int]]) -> float:
    """
    Calculates sequential costs based on previous events.

    Args:
        event_idx: Current event index
        seq_idx: Current sequence index
        events: All events
        sequences: All sequences

    Returns:
        float: Sequential costs
    """
    if event_idx == 0:  # First event
        return 0.0

    prev_event_time = events.iloc[event_idx - 1][24]
    current_start = sequences[seq_idx][0]

    if current_start < prev_event_time:
        return 1.0

    return 0.0


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
    # Critical events (must be in the correct phase)
    critical_events = {
        "score_change": 1.0,
        "shot_saved": 0.9,
        "shot_blocked": 0.9,
        "seven_m_awarded": 0.8,
        "shot_off_target": 0.7,
        "technical_ball_fault": 0.7,
        "technical_rule_fault": 0.7,
        "steal": 0.7
    }

    # Less critical events
    non_critical_events = {
        "yellow_card": 0.4,
        "suspension": 0.3

    }

    # Determine base costs based on event type
    base_cost = critical_events.get(event_type,
                                    non_critical_events.get(event_type, 0.5))

    # Check phase compatibility
    if ((phase in (1, 3) and competitor == dv.Team.A) or
            (phase in (2, 4) and competitor == dv.Team.B)):
        return 0.0  # Correct phase

    return base_cost  # Wrong phase


def sync_events_cost_function(events: pd.DataFrame,
                              sequences: List[Tuple[int, int, int]]
                              ) -> pd.DataFrame:
    """
    Synchronizes events using a cost function.

    Args:
        events: DataFrame with event data
        sequences: List of sequence tuples

    Returns:
        pd.DataFrame: Synchronized events
    """
    cost_matrix = calculate_cost_matrix(events, sequences)

    # Find optimal assignment for each event
    for i, _ in enumerate(events.values):
        event_costs = cost_matrix[i]
        best_sequence_idx = np.argmin(event_costs)

        if event_costs[best_sequence_idx] < np.inf:
            start, end, _ = sequences[best_sequence_idx]
            events.iloc[i, 24] = start + (end - start) // 2

    return events
