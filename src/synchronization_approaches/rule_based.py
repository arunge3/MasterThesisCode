
"""
    This module contains the rule-based synchronization approach for
    handball event timelines.
    Author:
        @Annabelle Runge
    Date:
        2025-04-29
    """
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from variables import data_variables as dv


def synchronize_events_fl_rule_based(events: Any,
                                     sequences: list[tuple[int, int, int]]
                                     ) -> tuple[list[Any], list[Any]]:
    """
    Synchronizes events with the given sequences by updating the event times
    and phases based on specific conditions.
    Args:
        events (list[Any]): A list of events where each event is expected to
        be a list with specific attributes.
        sequences (list[tuple[int, int, int]]): A list of sequences where each
        sequence is a tuple containing three integers.
    Returns:
        tuple[list[Any], list[Any]]: A tuple containing the updated list of
        events and the original list of sequences.
    """
    event_handlers: Dict[str, Callable[[Any], int]] = {
        "score_change": lambda e: handle_score_change(e, events, sequences),
        "seven_m_missed": lambda e: handle_seven_m_missed(e, sequences),
        "timeout": lambda e: handle_timeout(e, sequences),
        "timeout_over": lambda e: handle_timeout_over(e, sequences, events),
        "seven_m_awarded": lambda e: handle_phase_correction(e, sequences),
        "shot_off_target": lambda e: handle_phase_correction(e, sequences),
        "shot_saved": lambda e: handle_phase_correction(e, sequences),
        "shot_blocked": lambda e: handle_phase_correction(e, sequences),
        "technical_ball_fault": lambda e: handle_phase_correction(e,
                                                                  sequences),
        "technical_rule_fault": lambda e: handle_phase_correction(e,
                                                                  sequences),
        # "yellow_card": lambda e: handle_phase_correction(e, sequences)
    }

    possession_change_events = {"yellow_card",
                                "suspension", "steal", "substitution"}

    for idx in range(len(events)):
        if events.iloc[idx, 0] in event_handlers:
            new_time = event_handlers[events.iloc[idx, 0]](events.iloc[idx])
            if new_time is not None:
                events.iloc[idx, 24] = new_time
        elif events.iloc[idx, 0] in possession_change_events:
            opponent = (dv.Team.A if events.iloc[idx, 25] == dv.Team.B
                        else dv.Team.B)

            new_time = calculate_correct_phase_fl(
                events.iloc[idx, 24], sequences, opponent)
            if new_time is not None:
                events.iloc[idx, 24] = new_time

    return events, sequences


def handle_score_change(event: np.ndarray[Any, Any], events: Any,
                        sequences: list[tuple[int, int, int]]) -> int:
    """
    Handles score change events by calculating the appropriate phase.

    Args:
        event (dict): The event dictionary containing event information.
            event[24] represents the event time
            event[21] represents the team (home/away)
        events (list[dict]): List of all events in the match.
        sequences (list[tuple[int, int, int]]): List of sequences
        where each tuple contains
            start time, end time and phase number.
    Returns:
        int: The event time.
    """
    if str(give_last_event_fl(events, event.values[24])) != "seven_m_awarded":
        return calculate_correct_phase_fl(
            event.values[24], sequences, event.values[25])

    return calculate_inactive_phase_fl(event.values[24], sequences)


def handle_seven_m_missed(event: Any,
                          sequences: list[tuple[int, int, int]]) -> int:
    """
    Handles seven_m_missed events by calculating the appropriate phase.

    Args:
        event (dict): The event dictionary containing event information.
            event[24] represents the event time
            event[21] represents the team (home/away)
        sequences (list[tuple[int, int, int]]): List of sequences
        where each tuple contains
            start time, end time and phase number.
    Returns:
        int: The event time.
    """
    return calculate_inactive_phase_fl(event.values[24], sequences)


def handle_timeout(event: np.ndarray,
                   sequences: list[tuple[int, int, int]]
                   ) -> int:
    """
    Handles timeout events by calculating the appropriate phase.

    Args:
        event (dict): The event dictionary containing event information.
            event[24] represents the event time
            event[21] represents the team (home/away)
        sequences (list[tuple[int, int, int]]): List of sequences
        where each tuple contains
            start time, end time and phase number.
    Returns:
        int: The event time.
    """
    return calculate_timeouts_fl(event.values[24], sequences,
                                 event.values[25], event)


def handle_timeout_over(event: dict[Any, Any],
                        sequences: list[tuple[int, int, int]],
                        events: list[Any]
                        ) -> int:
    """
    Handles timeout over events by calculating the appropriate
    phase after a timeout ends
    Args:
        event (dict): The event dictionary containing event
        information.
            event[24] represents the event time
            event[21] represents the team (home/away)
        sequences (list[tuple[int, int, int]]): List of sequences where
            each tuple contains
            start time, end time and phase number.
        events (list[dict]): List of all events in the match.

    Returns:
        None: The function modifies the event in place by calling
        calculate_timeouts_over_fl
    """
    return calculate_timeouts_over_fl(sequences, event, events)


def handle_phase_correction(event: dict[Any, Any],
                            sequences: list[tuple[int, int, int]],
                            ) -> int:
    """
    Handles phase correction for an event by calculating the correct phase.
    Args:
        event (dict): The event dictionary containing event information.
            event[24] represents the event time
            event[21] represents the team (home/away)
        sequences (list[tuple[int, int, int]]): List of sequences
        where each tuple contains
            start time, end time and phase number.

    Returns:
        None: The function modifies the event in place by calling
        calculate_correct_phase_fl
    """
    return calculate_correct_phase_fl(
        event[24], sequences, event[25])


def give_last_event_fl(events: pd.DataFrame, time: int) -> Any:
    """
    Returns the last event from the list of events that occurred before the
    given time, excluding certain types of events.
    Args:
        events (List[Any]): A list of event dictionaries.
        time (int): The time threshold to compare events against.
    Returns:
        Any: The last event that occurred before the given time and is not of
        type "suspension", "yellow_card", "red_card", or "suspension_over".
        Returns None if no such event is found.
    """
    events = events.sort_values(
        by=events.columns[24])
    event: np.ndarray[Any, Any]
    for event in reversed(events.values):
        if event[24] < time:

            if event[0] not in [
                "suspension",
                "yellow_card",
                "red_card",
                "suspension_over",
            ]:
                return event
    return None


def calculate_correct_phase_fl(
    time: int, sequences: list[tuple[int, int, int]], team_ab: dv.Team
) -> int:
    """
    Determines the correct phase for a given event based on the provided time,
    sequences, and team.
    Args:
        time (int): The time of the event.
        sequences (list of tuples): A list of tuples where each tuple
            contains the start time, end time, and phase.
        team_ab (str): The team identifier, either "A" or "B".
        event (dict): The event dictionary which may be modified with a new
            time if the phase is incorrect.
    Returns:
        int: The event time.
    """
    phase: int
    start: int
    end: int
    for start, end, phase in sequences:
        if start <= time < end:
            break
    if ((phase in (1, 3)) and team_ab == dv.Team.A) or (
        (phase in (2, 4)) and team_ab == dv.Team.B
    ):
        print("correct Phase")

    else:
        new_time = search_phase_fl(time, sequences, team_ab)
        if new_time is not None:
            return new_time
    return time


def search_phase_ml_fl(time: int,
                       sequences: list[tuple[int, int, int]],
                       competitor: dv.Team
                       ) -> int:
    """
    Searches for the appropriate phase for a competitor, first checking
    the current phase, then the next, and finally the previous phases.


    Args:
        time (int): The time for which the phase is being searched.
        sequences (list): List of sequences (start, end, phase).
        competitor (dv.Opponent): The competitor being checked (HOME/AWAY).

    Returns:
        int: Time in the appropriate phase.

    Raises:
        ValueError: If no appropriate phase is found.
    """
    # Prüfe aktuelle Phase
    current_sequence = (-1, -1, -1)
    current_idx = -1

    for idx, (start, end, phase) in enumerate(sequences):
        if start <= time < end:
            current_sequence = (start, end, phase)
            current_idx = idx
            break

    if current_sequence != (-1, -1, -1):
        # Prüfe ob aktuelle Phase passt
        if ((current_sequence[2] in (1, 3) and
             competitor == dv.Team.A) or
                (current_sequence[2] in (2, 4)
                 and competitor == dv.Team.B)):
            return time

        # Prüfe nächste Phase falls vorhanden
        if current_idx < len(sequences) - 1:
            next_phase = sequences[current_idx + 1][2]
            if ((next_phase in (1, 3) and competitor == dv.Team.A) or
                    (next_phase in (2, 4) and competitor == dv.Team.B)):
                return sequences[current_idx + 1][0]

    # Prüfe vorherige Phasen
    for start, end, phase in reversed(sequences):
        if end <= time:
            if ((phase in (1, 3) and competitor == dv.Team.A) or
                    (phase in (2, 4) and competitor == dv.Team.B)):
                return end - 1

    raise ValueError("Keine passende Phase gefunden!")


def search_phase_fl(time: int,
                    sequences: list[tuple[int, int, int]],
                    competitor: dv.Team
                    ) -> int:
    """
    Searches for the last matching (active) phase before a given time for a

    specified competitor.
    Args:
        time (int): The time before which to search for the phase.
        sequences (list of tuples): A list of tuples where each tuple contains
                                    (start_time, end_time, phase).
        competitor (str): The competitor for whom the phase is being searched.
                Should be either "A" or "B".
    Returns:
        int: The end time of the last matching phase before the given
            time for the specified competitor.
    Raises:
        ValueError: If no valid phase is found for the given time.
    """
    # Go through sequences in reverse to find the last matching
    # phase before the given `time`
    end: int
    phase: int
    print(time)
    for _, end, phase in reversed(sequences):
        if end <= time:
            if (phase in (1, 3)) and competitor == dv.Team.A:
                return end - 1  # Return the end of this phase
            if (phase in (2, 4)) and competitor == dv.Team.B:
                return end - 1  # Return the end of this phase for

    print("No valid phase found for the given time!")
    return time


def calculate_inactive_phase_fl(
    time: int, sequences: List[Tuple[int, int, int]]
) -> int:
    """
    Calculate the inactive phase for a given time based on sequences.
    If the phase is 0, the function returns the time. If the phase is not 0,
    the function returns the end time minus one of the last sequence where the
    phase is 0. If no valid match is found, the function returns None.
    Args:
        time (int): The time to check against the sequences.
        sequences (List[Tuple[int, int, int]]): A list of tuples where each
            tuple contains (start, end, phase) representing the start time,
            end time, and phase respectively.

    Returns:
        int: The end time minus one of the last sequence where
            the phase is 0.
    Raises:
        ValueError: If no valid phase is found for inactive phase calculation.
    """
    for start, end, phase in sequences:
        if start <= time < end:
            if phase == 0:
                print("correct Phase")
                return time  # Indicates phase is active and valid.
            break

    # Reverse lookup if phase is not 0
    for _, end, phase in reversed(sequences):
        if end <= time:
            if phase == 0:
                return end - 1

    raise ValueError("No valid phase found for inactive phase calculation!")


def calculate_timeouts_fl(time: int, sequences: list[tuple[int, int, int]],
                          team_ab: dv.Team, event: np.ndarray
                          ) -> int:
    """
    Calculate the appropriate timeout time based on the given
    timeout-event and sequences.
    Args:

        time (int): The current time in the event.
        sequences (list of tuples): A list of tuples where each
            tuple contains (start, end, phase) representing the
            start time, end time, and phase of a sequence.
        team_ab (str): The team identifier, either "A" or "B".
        event (dict): A dictionary containing event details.
                    Must include a key "type" with value "timeout".
    Returns:
        int: The calculated timeout time if a valid phase is found
    Raises:
        ValueError: If no valid phase is found for the timeout event.
    """

    if event.values[0] == "timeout":
        phase_timeout: int
        start: int
        end: int
        for start, end, phase in sequences:
            if start <= time < end:
                phase_timeout = phase
                break
        if phase_timeout == 0:
            print("correct Phase")
            return time
        if ((phase_timeout in (1, 3) and (team_ab == dv.Team.A))
                or (phase_timeout in (2, 4) and team_ab == dv.Team.B)):
            if int(time) == int(end - 1):
                print("correct Phase")
                return time

            return end - 1
        # Go through sequences in reverse to find the last matching phase
        # before `time`
        for _, end, phase in reversed(sequences):
            if end <= time:
                if (phase in (1, 3)) and (team_ab == dv.Team.A):
                    return end - 1
                if (phase in (2, 4)) and (team_ab == dv.Team.B):
                    return end - 1

    raise ValueError("No valid phase found for timeout event!")


def calculate_timeouts_over_fl(sequences: list[tuple[int, int, int]],
                               event: np.ndarray, events: list[Any]
                               ) -> int:
    """
    Calculate the time of a timeout_over event within given sequences
    based on the phase and calculate if the last event was a timeout.
    Args:

        sequences (list of tuples): A list of tuples where each tuple contains
            the start time, end time, and phase of a sequence.
        event (dict): A dictionary representing the current event with keys
            such as "type" and "time".
        events (list): A list of dictionaries representing all events
            with keys such as "type" and "time".
    Returns:
        int: The time of the timeout over event if conditions are met.
    Raises:
        ValueError: If the events are in the wrong order.
        ValueError: If no valid phase is found for the timeout_over event.
    """

    if event.values[0] == "timeout_over":
        time: int
        time = event.values[24]
        start: int
        end: int
        phase: int
        for start, end, phase in sequences:
            if start <= time < end:
                break
        if phase == 0:
            lastevent = give_last_event_fl(events, time)
            if lastevent[0] == "timeout":
                return time
            print("No valid phase found for timeout_over event!")
        time_inactive = calculate_inactive_phase_fl(time, sequences)
        if time_inactive is not None:
            lastevent = give_last_event_fl(events, time_inactive)
            if lastevent[0] == "timeout":
                return time_inactive
    print("No valid phase found for timeout_over event!")
    return time
