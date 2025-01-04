from datetime import datetime as dt
from typing import Any, List, Tuple

import numpy as np
import pytz  # type: ignore
from floodlight.core.code import Code

import help_functions.reformatjson_methods as helpFuctions
from existing_code.rolling_mode import rolling_mode


def adjustTimestamp(match_id: int) -> tuple[Any, dict[Any, Any]]:
    """
    Adjusts the timestamps of events in a match to align with the
    positional data timeframe.
    This function performs the following steps:
    1. Retrieves various paths and parameters related to the match
    using the match_id.
    2. Loads the first timestamp of the positional data.
    3. Loads and reformats the event data to adjust timestamps based on
    the positional data.
    4. Converts the first positional data timestamp to a datetime object.
    5. Adjusts the timestamps of each event to align with the positional
    data timeframe.
    Args:
        match_id (int): The unique identifier for the match.
    Returns:
        Tuple: A tuple containing the adjusted events and team information.
    """
    # Paths
    (
        _, path_timeline, _, positions_path, cut_h1, offset_h2,
        first_vh2, _
    ) = helpFuctions.get_paths_by_match_id(match_id)
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = helpFuctions.load_first_timestamp_position(positions_path)

    # Framerate of the video
    fps_video = 29.97
    # Load event data and adjust timestamps
    event_json = helpFuctions.reformatJson_Time_only(
        path_timeline, first_time_pos_str, cut_h1, offset_h2,
        first_vh2, fps_video
    )

    competitors = event_json["sport_event"]["competitors"]
    # Extract team names and qualifiers
    team_info = {team["name"]: team["qualifier"] for team in competitors}
    events = event_json.get("timeline", [])

    # Match start timestamp
    first_time_stamp_event = helpFuctions.getFirstTimeStampEvent(path_timeline)
    print("match_start_datetime:", first_time_stamp_event)

    # timezone
    utc_timezone = pytz.utc

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_date = dt.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=utc_timezone)
    print("positional_data_start_date:", positional_data_start_date)

    # Change the time of the events to the timeframe of the positional data
    for event in events:
        # time = add_threshold_to_time(event)
        time = event["time"]
        event_time_seconds = (time - cut_h1) / fps_video
        event_absolute_timestamp = (
            positional_data_start_timestamp + event_time_seconds)
        event_timestamp_date = (dt.fromtimestamp(event_absolute_timestamp)
                                .replace(tzinfo=utc_timezone))
        print("event_timestamp_date:", event_timestamp_date)
        event_timeframe = (
            event_timestamp_date - positional_data_start_date
        ).seconds * fps_positional
        event["time"] = event_timeframe

    return events, team_info


def calculate_sequences(match_id: int, base_path: str = "D:\\Handball\\",
                        season: str = "season_20_21") -> list[Any]:
    """
    Calculate sequences of game phases for a given match.
    Args:
        match_id (int): The identifier for the match.
    Returns:
        list: A list of sequences where each sequence is represented as a
            tuple (start_frame, end_frame).
            Only sequences longer than one frame duration are included.
    """
    sequences: list[Any]
    # Paths
    _, _, _, positions_path, _, _, _, match = (
        helpFuctions.get_paths_by_match_id(match_id))
    _, _, fps_positional = helpFuctions.load_first_timestamp_position(
        positions_path)
    phase_predictions_path = f"{base_path}HBL_Slicing\\{season}\\{match}.npy"

    # Load positional data and phase predictions
    predictions = np.load(phase_predictions_path)
    predictions = rolling_mode(predictions, 101)
    slices = Code(
        predictions,
        "match_phases",
        {0: "inac", 1: "CATT-A", 2: "CATT-B", 3: "PATT-A", 4: "PATT-B"},
        fps_positional,
    )

    # get Sequences of the game phases
    sequences = slices.find_sequences(return_type="list")
    sequences = [x for x in sequences if x[1] - x[0] > slices.framerate]

    return sequences


def synchronize_events(events: list[Any],
                       sequences: list[tuple[int, int, int]],
                       team_info: dict[str, str]
                       ) -> tuple[list[Any], list[Any]]:
    """
    Synchronize events with sequences and team information.
    This function processes a list of events and sequences, and synchronizes
    them based on the provided team information and timestamps.
    It assigns teams based on alphabetical order, determines their
    locations (home or away), and maps events to the corresponding teams.
    It is the rule-based approach to synchronize events with sequences.
    For each event type, it calculates the correct timestamp based on the
    phase of the game and the team involved.
    Args:
        events (list): A list of event dictionaries, where each
            dictionary contains event details such as type, time, and
            competitor.
        sequences (list): A list of sequences to be synchronized with the
            events.
        team_info (dict): A dictionary containing team names as keys and
            their locations (home or away) as values.
    Returns:
        tuple: A tuple containing the updated events and sequences.
    """

    # Sort team names alphabetically
    team_names = list(team_info.keys())
    sorted_teams = sorted(team_names)

    # Assign Team A and Team B based on alphabetical order
    team_a = sorted_teams[0]
    team_b = sorted_teams[1]

    # Determine home or away for Team A and Team B
    team_a_location = team_info[team_a]
    team_b_location = team_info[team_b]

    print(f"Team A: {team_a} ({team_a_location})")
    print(f"Team B: {team_b} ({team_b_location})")
    # Create a mapping of location to Team A or Team B
    location_to_team = {team_a_location: "A", team_b_location: "B"}

    for event in events:
        competitor_location = event.get("competitor")
        if competitor_location in location_to_team:
            team_ab = location_to_team[
                competitor_location
            ]  # Map "home"/"away" to "A" or "B"
            print(
                f"Event Type: {event['type']}, Competitor: Team "
                f"{team_ab}({competitor_location})")
        else:
            # Handle events without a competitor if necessary
            print(f"Event Type: {event['type']}, Competitor: None")
        type = event["type"]
        time = event["time"]
        if type == "score_change":
            if str(give_last_event) != "seven_m_awarded":
                calculate_correct_phase(
                    time, sequences, team_ab, event)
                # event["time"] = event_calc["time"]
            else:
                event["time"] = calculate_inactive_phase(time, sequences)
        elif type == "seven_m_missed":
            event["time"] = calculate_inactive_phase(time, sequences)
        elif type == "timeout":
            event["time"] = calculate_timeouts(time, sequences, team_ab, event)
        elif (type == "yellow_card" or type == "suspension" or
              type == "steal" or type == "substitution"):
            if team_ab == "A":
                calculate_correct_phase(time, sequences, "B", event)
            else:
                calculate_correct_phase(time, sequences, "A", event)
        elif (
            type == "seven_m_awarded"
            or type == "shot_off_target"
            or type == "seven_m_missed"
            or type == "shot_saved"
            or type == "shot_blocked"
            or type == "technical_ball_fault"
            or type == "technical_rule_fault"
            or type == "yellow_card"
        ):
            calculate_correct_phase(
                time, sequences, team_ab, event)
        elif type == "timeout_over":
            event["time"] = calculate_timeouts_over(sequences, event, events)
    return events, sequences


def searchPhase(time: int,
                sequences: list[tuple[int, int, int]], competitor: str
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
    for _, end, phase in reversed(sequences):
        if end <= time:
            if (phase == 1 or phase == 3) and competitor == "A":
                return end - 1  # Return the end of this phase
            elif (phase == 2 or phase == 4) and competitor == "B":
                return end - 1  # Return the end of this phase for
    raise ValueError("No valid phase found for the given time!")


def give_last_event(events: list[Any],
                    time: int) -> Any:
    """
    Returns the last event from the list of events that occurred
    before the given time, excluding certain types of events.
    Args:
        events (list): A list of event dictionaries, where each
                                dictionary contains information about an
                                event, including a "time" key and a
                                "type" key.
        time (int): The time threshold to compare events against.
    Returns:
        dict: The last event dictionary that occurred before or at the
                    given time and is not of type "suspension", "yellow_card",
                    "red_card", or "suspension_over".
    Raises:
        ValueError: If no valid event is found before the given time.
    """
    event: dict[Any, Any]
    for event in reversed(events):
        if event["time"] < time:
            if event["type"] not in [
                "suspension",
                "yellow_card",
                "red_card",
                "suspension_over",
            ]:
                return event
    raise ValueError("No valid event found before the given time!")


def add_threshold_to_time(event: dict[Any, Any]) -> int:
    """
    Adjusts the event time by adding a predefined threshold based
    on the event type. The threshold are based on the mean difference
    of the manually annotated events.
    Args:
        event (dict[Any, Any]): A dictionary containing event details.
                                It must have a "type" key indicating
                                the event type and a "time" key
                                indicating the event time.
    Returns:
        int: The adjusted event time after adding the threshold. If the event
            type is not found in the predefined thresholds, the original event
            time is returned.
    """

    # Define the time thresholds for each event type
    thresholds = {
        "break_start": -359.4,
        "match_ended": -431.7,
        "period_score": -412.5,
        "red_card": -233.5,
        "score_change": -108.76,
        "seven_m_awarded": -468.59,
        "seven_m_missed": -74.0,
        "shot_blocked": -311.92,
        "shot_off_target": -236.86,
        "shot_saved": -251.31,
        "steal": -256.58,
        "substitution": -5.03,
        "suspension": -385.53,
        "suspension_over": -4.16,
        "technical_ball_fault": -244.72,
        "technical_rule_fault": -258.31,
        "timeout": -283.09,
        "timeout_over": -29.18,
        "yellow_card": -267.82,
    }

    threshold = thresholds.get(str(event["type"]), 0)
    returnTime: int
    returnTime = event["time"] + threshold
    return returnTime


def calculate_inactive_phase(
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


def calculate_timeouts(time: int, sequences: list[tuple[int, int, int]],
                       team_ab: str, event: dict[Any, Any]
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

    if event["type"] == "timeout":
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
        elif ((phase_timeout == 1 or phase_timeout == 3 and team_ab == "A")
              or (phase_timeout == 2 or phase_timeout == 4
                  and team_ab == "B")):
            if int(time) == int(end - 1):
                print("correct Phase")
                return time
            else:
                return end - 1
        else:
            # Go through sequences in reverse to find the last matching phase
            # before `time`
            for _, end, phase in reversed(sequences):
                if end <= time:
                    if (phase == 1 or phase == 3) and team_ab == "A":
                        return (
                            end - 1
                        )  # Return the end of this phase for competitor "A"
                    elif (phase == 2 or phase == 4) and team_ab == "B":
                        return (
                            end - 1
                        )  # Return the end of this phase for competitor "B"
    raise ValueError("No valid phase found for timeout event!")


def calculate_timeouts_over(sequences: list[tuple[int, int, int]],
                            event: dict[Any, Any], events: list[Any]
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

    if event["type"] == "timeout_over":
        time: int
        time = event["time"]
        start: int
        end: int
        phase: int
        for start, end, phase in sequences:
            if start <= time < end:
                break
        if phase == 0:
            # TODO Ich möchte berechnen dass das letzte Event
            # das Timeout war und das in der Zeit dazwischen
            # nur inaktive phase war
            # TODO ist noch flasch gibt das flasche event zurück
            lastevent = give_last_event(events, time)
            if lastevent["type"] == "timeout":
                return time
            else:
                raise ValueError("Events are in wrong order!")
        else:
            time_inactive = calculate_inactive_phase(time, sequences)
            if time_inactive is not None:
                lastevent = give_last_event(events, time_inactive)
                if lastevent["type"] == "timeout":
                    return time_inactive
    raise ValueError("No valid phase found for timeout_over event!")


def checkSamePhase(
    startTime: int, endtime: int,
    sequences: list[tuple[int, int, int]], phase: int
) -> int:
    """
    Check if both the start and end time of a given interval falls
    within the same phase and the same sequence.
    Args:
        startTime (int): The start time of the interval to check.
        endtime (int): The end time of the interval to check.
        sequences (list of tuples): A list of tuples where each tuple
                                contains (start, end, phase)
                                representing the start time,
                                end time, and phase of a
                                sequence.
        phase (int): The phase to check against.
    Returns:
        int: Returns the end time of the interval if it falls
            within the specified phase.
    Raises:
        ValueError: If no valid phase is found for the given interval.
    """
    start: int
    end: int
    phaseAct: int
    for start, end, phaseAct in sequences:
        if startTime >= start and endtime < end:
            if phase == phaseAct:
                return endtime
            else:
                return -1
        elif startTime <= start and endtime >= end:
            return end
    raise ValueError("No valid phase found for the given interval!")


def calculate_correct_phase(
    time: int, sequences: list[tuple[int, int, int]], team_ab: str,
    event: dict[Any, Any]
) -> dict[Any, Any]:
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
        Dict: The event dictionary with the updated time if the phase is
            incorrect.
    """
    # TODO kann man anhand der Positionsdaten ermitteln, ob ein Ball im
    # Tor war oder nicht?
    # INlusive Zeitstempel?
    # DID den mean error anwenden bei allen aktionen. Weil alle outliers
    # liegen unter dem mean error

    # Find the y value on the continuous line for this event's time (t_start)
    # Define positions for each phase
    phase: int
    start: int
    end: int
    for start, end, phase in sequences:
        if start <= time < end:
            break
    if ((phase == 1 or phase == 3) and team_ab == "A") or (
        (phase == 2 or phase == 4) and team_ab == "B"
    ):
        print("correct Phase")

    else:
        new_time = searchPhase(time, sequences, team_ab)
        if new_time is not None:
            event["time"] = new_time
            return event
    return event


def adjustTimestamp_baseline(match_id: int) -> tuple[Any, dict[Any, Any]]:
    # Paths
    (
        _, path_timeline, _, positions_path, cut_h1, offset_h2,
        first_vh2, _
    ) = helpFuctions.get_paths_by_match_id(match_id)
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = helpFuctions.load_first_timestamp_position(positions_path)

    # Framerate of the video
    fps_video = 29.97
    # Load event data and adjust timestamps
    event_json = helpFuctions.reformatJson_Time_only(
        path_timeline, first_time_pos_str, cut_h1, offset_h2,
        first_vh2, fps_video
    )

    competitors = event_json["sport_event"]["competitors"]
    # Extract team names and qualifiers
    team_info = {team["name"]: team["qualifier"] for team in competitors}
    events = event_json.get("timeline", [])

    # Match start timestamp
    first_time_stamp_event = helpFuctions.getFirstTimeStampEvent(path_timeline)
    print("match_start_datetime:", first_time_stamp_event)

    # timezone
    utc_timezone = pytz.utc

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_date = dt.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=utc_timezone)
    print("positional_data_start_date:", positional_data_start_date)

    # Change the time of the events to the timeframe of the positional data
    for event in events:
        time = add_threshold_to_time(event)
        event_time_seconds = (time - cut_h1) / fps_video
        event_absolute_timestamp = (
            positional_data_start_timestamp + event_time_seconds)
        event_timestamp_date = (dt.fromtimestamp(event_absolute_timestamp)
                                .replace(tzinfo=utc_timezone))
        print("event_timestamp_date:", event_timestamp_date)
        event_timeframe = (
            event_timestamp_date - positional_data_start_date
        ).seconds * fps_positional
        event["time"] = event_timeframe

    return events, team_info


def getEvents(match_id: int) -> tuple[Any, dict[Any, Any]]:
    # Paths
    (
        _, path_timeline, _, positions_path, cut_h1, offset_h2,
        first_vh2, _
    ) = helpFuctions.get_paths_by_match_id(match_id)
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = helpFuctions.load_first_timestamp_position(positions_path)

    # Framerate of the video
    fps_video = 29.97
    # Load event data and adjust timestamps
    event_json = helpFuctions.reformatJson_Time_only(
        path_timeline, first_time_pos_str, cut_h1, offset_h2,
        first_vh2, fps_video
    )

    competitors = event_json["sport_event"]["competitors"]
    # Extract team names and qualifiers
    team_info = {team["name"]: team["qualifier"] for team in competitors}
    events = event_json.get("timeline", [])

    # Match start timestamp
    first_time_stamp_event = helpFuctions.getFirstTimeStampEvent(path_timeline)
    print("match_start_datetime:", first_time_stamp_event)

    # timezone
    utc_timezone = pytz.utc

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_date = dt.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=utc_timezone)
    print("positional_data_start_date:", positional_data_start_date)

    # Change the time of the events to the timeframe of the positional data
    for event in events:
        time = event["time"]
        event_time_seconds = (time - cut_h1) / fps_video
        event_absolute_timestamp = (
            positional_data_start_timestamp + event_time_seconds)
        event_timestamp_date = (dt.fromtimestamp(event_absolute_timestamp)
                                .replace(tzinfo=utc_timezone))
        print("event_timestamp_date:", event_timestamp_date)
        event_timeframe = (
            event_timestamp_date - positional_data_start_date
        ).seconds * fps_positional
        event["time"] = event_timeframe

    return events, team_info


def synchronize_events_ml() -> None:
    return None
