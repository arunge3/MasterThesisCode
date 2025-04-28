from typing import Any

from synchronization_approaches.rule_based import search_phase_ml_fl


def correct_events_fl(events: Any, sequences: list[tuple[int, int, int]]
                      ) -> tuple[Any, list[tuple[int, int, int]]]:
    """
    Corrects ML-based event synchronization with Floodlight data.

    Args:
        events: The event data
        sequences: List of sequences (start, end, phase)
    Returns:
        Tuple of corrected events and sequences
    """
    for idx, event in enumerate(events.values):
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            events.iloc[idx, 24] = search_phase_ml_fl(
                event[24], sequences, event[25])
    return events, sequences
