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
    Berechnet die Kostenmatrix für die Event-Synchronisation.

    Args:
        events: DataFrame mit Event-Daten
        sequences: Liste von Sequenz-Tupeln (start, end, phase)

    Returns:
        np.ndarray: Kostenmatrix
    """

    cost_matrix = np.full((len(events), len(sequences)), np.inf)

    for i, event in enumerate(events.values):
        event_time = event[22]  # Zeitstempel des Events
        event_type = event[0]   # Event-Typ
        competitor = event[21]  # Team (HOME/AWAY)

        for j, (start, end, phase) in enumerate(sequences):
            # Grundkosten basierend auf zeitlicher Distanz
            temporal_cost = min(abs(event_time - start),
                                abs(event_time - end))

            # Phasenbasierte Kosten
            phase_cost = calculate_phase_cost(phase, competitor,
                                              event_type)

            # Gesamtkosten
            total_cost = temporal_cost + phase_cost
            cost_matrix[i, j] = total_cost

    return cost_matrix


def calculate_phase_cost(phase: int, competitor: dv.Opponent,
                         event_type: str) -> float:
    """
    Berechnet die phasenbasierten Kosten für ein Event.

    Args:
        phase: Aktuelle Phase
        competitor: Team (HOME/AWAY)
        event_type: Typ des Events

    Returns:
        float: Phasenkosten
    """
    # Offensive Phasen für HOME: 1,3 und für AWAY: 2,4
    if event_type in ["score_change", "shot_saved", "shot_off_target",
                      "shot_blocked", "technical_rule_fault",
                      "seven_m_awarded"]:
        if ((phase in (1, 3) and competitor == dv.Opponent.HOME) or
                (phase in (2, 4) and competitor == dv.Opponent.AWAY)):
            return 0.0
        return 1000.0

    return 0.0


def sync_events_cost_function(events: pd.DataFrame,
                              sequences: List[Tuple[int, int, int]]
                              ) -> pd.DataFrame:
    """
    Synchronisiert Events mittels Kostenfunktion.

    Args:
        events: DataFrame mit Event-Daten
        sequences: Liste von Sequenz-Tupeln

    Returns:
        pd.DataFrame: Synchronisierte Events
    """
    cost_matrix = calculate_cost_matrix(events, sequences)

    # Optimale Zuordnung für jedes Event finden
    for i, _ in enumerate(events.values):
        event_costs = cost_matrix[i]
        best_sequence_idx = np.argmin(event_costs)

        if event_costs[best_sequence_idx] < np.inf:
            start, end, _ = sequences[best_sequence_idx]
            # Setze neuen Zeitstempel
            events.iloc[i, 22] = start + (end - start) // 2

    return events
