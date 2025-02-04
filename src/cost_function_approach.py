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

    # Maximale erlaubte Zeitdifferenz (in Sekunden)
    MAX_TIME_DIFF = 10

    for i, event in enumerate(events.values):
        event_time = event[24]  # Zeitstempel des Events
        event_type = event[0]   # Event-Typ
        competitor = event[25]  # Team (HOME/AWAY)

        for j, (start, end, phase) in enumerate(sequences):
            # Zeitdifferenz in Sekunden
            time_diff = event_time - start

            # Wenn die Zeitdifferenz zu groß ist, überspringen
            if abs(time_diff) > MAX_TIME_DIFF:
                continue

            # 1. Zeitliche Kosten mit exponentiellem Verfall
            temporal_cost = calculate_temporal_cost(time_diff)

            # 2. Phasenbasierte Kosten
            phase_cost = calculate_phase_cost(phase, competitor, event_type)

            # 3. Sequenzielle Kosten basierend auf vorherigen Events
            sequence_cost = calculate_sequential_cost(i, j, events, sequences)

            # Gesamtkosten (stark gewichtet auf zeitliche Komponente)
            total_cost = (
                0.7 * temporal_cost +  # Noch stärkere Gewichtung der Zeit
                0.2 * phase_cost +
                0.1 * sequence_cost
            )

            cost_matrix[i, j] = total_cost

    return cost_matrix


def calculate_temporal_cost(time_diff: float) -> float:
    """
    Berechnet zeitliche Kosten mit exponentiellem Verfall.

    Args:
        time_diff: Zeitdifferenz in Sekunden

    Returns:
        float: Zeitkosten
    """
    # Präferenz für frühere Zeitpunkte durch asymmetrische Behandlung
    if time_diff > 0:  # Event ist später als Start
        return float(1 - np.exp(-time_diff / 2))  # schneller Anstieg
    else:  # Event ist früher als Start
        return float(1 - np.exp(time_diff / 4))   # langsamerer Anstieg


def calculate_sequential_cost(event_idx: int, seq_idx: int,
                              events: pd.DataFrame,
                              sequences: List[Tuple[int, int, int]]) -> float:
    """
    Berechnet sequenzielle Kosten basierend auf vorherigen Events.

    Args:
        event_idx: Aktueller Event-Index
        seq_idx: Aktueller Sequenz-Index
        events: Alle Events
        sequences: Alle Sequenzen

    Returns:
        float: Sequenzkosten
    """
    if event_idx == 0:  # Erstes Event
        return 0.0

    # Prüfe relative Position zum vorherigen Event
    prev_event_time = events.iloc[event_idx - 1][24]
    current_start = sequences[seq_idx][0]

    # Wenn aktuelles Event vor dem vorherigen liegt, hohe Kosten
    if current_start < prev_event_time:
        return 1.0

    return 0.0


def calculate_phase_cost(phase: int, competitor: dv.Team,
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
    # Kritische Events (müssen in der richtigen Phase sein)
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

    # Weniger kritische Events
    non_critical_events = {
        "yellow_card": 0.4,
        "suspension": 0.3

    }

    # Bestimme Basis-Kosten basierend auf Event-Typ
    base_cost = critical_events.get(event_type,
                                    non_critical_events.get(event_type, 0.5))

    # Prüfe Phasen-Kompatibilität
    if ((phase in (1, 3) and competitor == dv.Team.A) or
            (phase in (2, 4) and competitor == dv.Team.B)):
        return 0.0  # Korrekte Phase

    return base_cost  # Falsche Phase


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
            events.iloc[i, 24] = start + (end - start) // 2

    return events
