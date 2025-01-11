import os
from datetime import datetime as dt
from enum import Enum
from typing import Any, List, Tuple

import matplotlib
import pandas as pd
import pytz  # type: ignore
from floodlight import Events
from floodlight.io.sportradar import read_event_data_json
from matplotlib import pyplot as plt

import help_functions
import help_functions.reformatjson_methods
from plot_functions import processing
from plot_functions.plot_phases import berechne_phase_und_speichern_fl


def create_event_objects(
        path_timeline: str,
        fps: float) -> Any:
    """
    Creates event streams for home and away teams from a given timeline file.
    Args:
        path_timeline (str): The file path to the timeline JSON file.
        fps (float): Frames per second to be used for adding frame clocks
        to events.
    Returns:
        dict[Events, Events]: A dictionary containing Events objects for
        home and away teams.
    """

    data = read_event_data_json(path_timeline)
    # Assuming your data structure is named `data`
    # Add 1800 seconds to the `gameclock` column for all events in segment HT2
    for team, events in data['HT2'].items():
        events.events['gameclock'] += 1800

    # Flatten the nested dictionary
    data = flatten_nested_events(data)

    # Create the Events objects for each group
    event_all = Events(events=data)
    # event_away = Events(events=away_team_df)

    event_all.add_frameclock(fps)

    event_all.events = event_all.events.sort_values(
        by=event_all.events.columns[22])

    # Create a filtered list for timeout and timeout_over
    filtered_test = []
    team = None

    for _, row in event_all.events.iterrows():
        if row[0] == "timeout":
            team = row[21]  # Store the team for the last timeout
        elif row[0] == "timeout_over" and row[21] != team:
            continue  # Skip this timeout_over if it doesn't match the team
        else:
            team = None
        filtered_test.append(row)

    # Create a new DataFrame from the filtered rows
    event_all.events = pd.DataFrame(
        filtered_test, columns=event_all.events.columns)

    print(event_all.events)

    return event_all


def flatten_nested_events(nested_events: dict[Any, Any]) -> pd.DataFrame:
    """
    Flattens a nested dictionary of events into a single DataFrame.
    Args:
        nested_events (dict[Any, Any]): A dictionary where the keys are
        segments and the values are dictionaries.
        These inner dictionaries have teams as keys and event objects as
        values. Each event object contains a DataFrame of events.
    Returns:
        pd.DataFrame: A DataFrame containing all events from the nested
        structure, with additional columns for segment and team.
    """

    all_events = []
    for segment, teams in nested_events.items():
        for team, events_obj in teams.items():
            df = events_obj.events
            df['segment'] = segment
            df['team'] = team
            if team == "Home":
                df['team'] = Opponent.HOME
            elif team == "Away":
                df['team'] = Opponent.AWAY
            else:
                df['team'] = Opponent.NONE

            # Add to the unified list
            all_events.append(df)

    # Combine all DataFrames into one
    all_events_df = (pd.concat(
        all_events, ignore_index=True)
        if all_events else pd.DataFrame())
# def flatten_nested_events(nested_events: dict[Any, Any]
#                           ) -> tuple[Any, Any]:
#     home_team_events = []
#     away_team_events = []

#     for segment, teams in nested_events.items():
#         for team, events_obj in teams.items():
#             df = events_obj.events
#             df['segment'] = segment
#             df['team'] = team

#             # Split into home, away, and unassigned
#             if team == 'Home':
#                 home_team_events.append(df)
#             elif team == 'Away':
#                 away_team_events.append(df)

#     # Combine all DataFrames into one
#     home_team_df = (pd.concat(
#         home_team_events, ignore_index=True)
#         if home_team_events else pd.DataFrame())
#     away_team_df = (pd.concat(
#         away_team_events, ignore_index=True)
#         if away_team_events else pd.DataFrame())

#     return home_team_df, away_team_df
    return all_events_df


def calculate_offset(first_event_time_str: str,
                     first_timestamp_pos: str,
                     pos_fps: float) -> int:
    """
    Calculates the offset between positions data and event data.
    It is based on the real timestamps from eventdata and positional data.
    And the offset to the videodata is used to calcualte the offset.
    Args:
        first_event_time_str (str): The timestamp of the first event in
        ISO format.
        first_timestamp_pos (str): The first timestamp position in ISO format.
        pos_fps (int): Frames per second of the position data.
    Returns:
        float: The synchronized time position in frames.
    """
    first_event_time = dt.fromisoformat(
        first_event_time_str).replace(tzinfo=pytz.utc)
    if isinstance(first_timestamp_pos, tuple):
        first_timestamp = first_timestamp_pos[0]
    else:
        first_timestamp_str = str(first_timestamp_pos)
        first_timestamp = dt.fromisoformat(first_timestamp_str).replace(
            tzinfo=pytz.utc
        )

    delta = first_event_time - first_timestamp

    synced_time_pos_fr = int(delta.seconds * pos_fps)
    return synced_time_pos_fr


def calculate_event_stream(match_id: int) -> tuple[Any, int, Any]:
    """
    Processes match data and returns event streams for home and away teams.
    Args:
        match_id (int): The ID of the match to process.
    Returns:
        tuple[Any, Any]: A tuple containing the event stream for the home team
        and the event stream for the away team. This types are Code objects
        from floodlight libary.
    This function performs the following steps:
    1. Retrieves various paths and parameters related to the match
    using the match ID.
    2. Loads the first timestamp of positional data and event data.
    3. Loads event data.
    4. Calculates the offset for the event timestamps.
    5. Adjusts the event timestamps to align with the
    positional data timeframe.
    6. Returns the adjusted event streams for both home and away teams.
    """

    (
        _, path_timeline, _, positions_path, _, _, _, _
    ) = help_functions.reformatjson_methods.get_paths_by_match_id(match_id)
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = help_functions.reformatjson_methods.load_first_timestamp_position(
        positions_path)

    # Load event data and adjust timestamps
    event_all = create_event_objects(path_timeline,
                                     fps_positional)

    # Match start timestamp
    first_time_stamp_event = event_all.events['time_stamp'][0]
    first_time_stamp_event = first_time_stamp_event.strftime(
        '%Y-%m-%d %H:%M:%S')
    print("match_start_datetime:", first_time_stamp_event)

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_timestamp = dt.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=pytz.utc)
    print("positional_data_start_date:", positional_data_start_timestamp)
    offset = calculate_offset(first_time_stamp_event,
                              first_time_pos_str,
                              fps_positional)
    event_all.events['frameclock'] = event_all.events['frameclock'] + offset

    event_stream_all = event_all.get_event_stream(fade=1)
    return event_stream_all, offset, event_all.events.values


class Approach(Enum):
    """
    Enum class representing different approaches for the synchronizatrion
    of gamephases and events.
    Attributes:
        RULE_BASED (str): Represents a rule-based approach.
        BASELINE (str): Represents a baseline approach.
        NONE (str): Represents no calculation.
        ML_BASED (str): Represents a machine learning-based approach.
    """

    RULE_BASED = "Rule-based Approach"
    BASELINE = "Baseline"
    NONE = "No Calcuation"
    ML_BASED = "Machine Learning Approach"


class Opponent(Enum):
    """
    Enum class representing the opponent in a game.
    Attributes:
        HOME (str): Represents the home team.
        AWAY (str): Represents the away team.
        NONE (str): Represents no opponent.
    """
    HOME = "Home"
    AWAY = "Away"
    NONE = "None"


matplotlib.use("TkAgg", force=True)


def plot_phases(match_id: int, approach: Approach
                = Approach.RULE_BASED) -> None:
    """
    Plots the phases of a handball match along with event markers.
    Args:
        match_id (int): The ID of the match.
    Returns:
        None
    This function performs the following steps:
    1. Loads paths and initial timestamps for the match.
    2. Converts event frame numbers to absolute timestamps.
    3. Loads positional data and phasse predictions.
    4. Calculates sequences of game phases.
    5. Defines positions and labels for each phase.
    6. Defines event colors based on categories.
    7. Initializes lists to hold x (time) and y (position) values for a
    continuous line.
    8. Fills in x_vals and y_vals for a continuous line.
    9. Creates the plot and adds event markers with labels from `type`.
    10. Customizes the plot and shows it.
    Note:
        The function assumes the existence of several helper functions
        and modules such as `helpFuctions`, `np`, `plt`, and `Code`.
    """

    base_path = r"D:\Handball\HBL_Events\season_20_21"
    datengrundlage = r"Datengrundlagen"
    datengrundlage = os.path.join(base_path, datengrundlage)
    sequences = processing.calculate_sequences(match_id)
    if approach == Approach.RULE_BASED:
        (_, _,
         events) = calculate_event_stream(23400263)
        events, sequences = synchronize_events_fl(
            events, sequences)

        new_name = str(match_id) + "_rb_fl.csv"
        datei_pfad = os.path.join(datengrundlage, r"rulebased", new_name)
    # elif (approach == Approach.ML_BASED):
    #     events, sequences = processing.synchronize_events_ml(
    #         events, sequences, team_info)
    #     new_name = str(match_id) + "_ml.csv"
    #     datei_pfad = os.path.join(base_path_grundlage, r"ml", new_name)
    elif approach == Approach.BASELINE:
        events, _ = processing.adjustTimestamp_baseline(match_id)
        new_name = str(match_id) + "_bl_fl.csv"
        datei_pfad = os.path.join(datengrundlage, r"baseline", new_name)
    elif approach == Approach.NONE:
        new_name = str(match_id) + "_none_fl.csv"
        datei_pfad = os.path.join(datengrundlage, r"none", new_name)
    else:
        raise ValueError("Invalid approach specified!")

    # Define positions for each phase
    phase_positions = {
        0: 2,  # (inac)
        1: 3,  # (CATT-A)
        2: 1,  # (CATT-B)
        3: 4,  # (PATT-A)
        4: 0,  # (PATT-B)
    }
    phase_labels = {2: "inac", 3: "CATT-A",
                    1: "CATT-B", 4: "PATT-A", 0: "PATT-B"}
    # Define event colors based on categories
    event_colors = {
        "score_change": "dodgerblue",
        "suspension": "purple",
        "suspension_over": "darkviolet",
        "technical_rule_fault": "gold",
        "technical_ball_fault": "orange",
        "steal": "limegreen",
        "shot_saved": "mediumblue",
        "shot_off_target": "crimson",
        "shot_blocked": "red",
        "seven_m_awarded": "deeppink",
        "seven_m_missed": "hotpink",
        "yellow_card": "yellow",
        "red_card": "darkred",
        "timeout": "cyan",
        "timeout_over": "cyan",
        "subsitution": "black",
        # Default for all other events
        "default": "grey",
    }
    # Initialize lists to hold x (time) and y (position) values for a
    # continuous line
    x_vals = []
    y_vals = []

    # Fill in x_vals and y_vals for a continuous line
    for start, end, phase in sequences:
        # Append start of phase
        x_vals.append(start)
        y_vals.append(phase_positions[phase])

        # Append end of phase
        x_vals.append(end)
        y_vals.append(phase_positions[phase])

    # Create the plot
    _, ax = plt.subplots(figsize=(14, 4))

    # Plot the continuous line
    ax.plot(x_vals, y_vals, color="black", linewidth=2)

    # Track labels to avoid duplicates in the legend
    added_labels = set()

    berechne_phase_und_speichern_fl(events, sequences, datei_pfad)
    # Add event markers with labels from `type`
    for event in events:
        color = event_colors.get(event[0], event_colors["default"])
        # Find the y value on the continuous line for this event's time
        event_y = None
        for start, end, phase in sequences:
            if start <= event[22] < end:
                event_y = phase_positions[phase]

                break
        # Plot event marker
        # ax.axvline(t_start, color="red", linestyle="--", linewidth=1)
        # Vertical line at event time
        if event_y is not None:
            ax.plot(
                event[22],
                event_y,
                "x",
                color=color,
                markersize=8,
                label=event[0] if event[0] not in added_labels else "",
            )
            print(event[22], event_y, event[0])
            added_labels.add(event[0])
    # Add legend
    ax.legend(title="Event Types", loc="upper right", bbox_to_anchor=(1.15, 1))

    # Customize the plot
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_yticks(sorted(set(phase_positions.values())))
    ax.set_yticklabels(
        [phase_labels[phase] for phase in sorted(phase_positions.keys())]
    )
    ax.set_xlabel("Timeframe")
    ax.set_title("Continuous Game phase Timeline")

    # Set x-axis limit to show only from 0 to 2000
    ax.set_xlim(6000, 50000)
    # Show plot
    plt.show()


def synchronize_events_fl(events: list[Any],
                          sequences: list[tuple[int, int, int]]
                          ) -> tuple[list[Any], list[Any]]:
    """
    Synchronizes events with the given sequences by updating the event times
    and phases based on specific conditions.
    Args:
        events (list[Any]): A list of events where each event is expected to
        be a list with specific indices representing different attributes.
        sequences (list[tuple[int, int, int]]): A list of sequences where each
        sequence is a tuple containing three integers.
    Returns:
        tuple[list[Any], list[Any]]: A tuple containing the updated list of
        events and the original list of sequences.
    The function processes each event in the events list and updates the event
    time or phase based on the event type and other conditions.
    The event types handled include "score_change", "seven_m_missed",
    "timeout", "yellow_card", "suspension", "steal", "substitution",
    "seven_m_awarded", "shot_off_target", "shot_saved", "shot_blocked",
    "technical_ball_fault", "technical_rule_fault", and "timeout_over".
    """
    for event in events:
        if event[0] == "score_change":
            if str(give_last_event_fl(events, event[22])) != "seven_m_awarded":
                calculate_correct_phase_fl(
                    event[22], sequences, event[21], event)
                # event["time"] = event_calc["time"]
            else:
                event[22] = calculate_inactive_phase_fl(event[22], sequences)
        elif event[0] == "seven_m_missed":
            event[22] = calculate_inactive_phase_fl(event[22], sequences)
        elif event[0] == "timeout":
            event[22] = calculate_timeouts_fl(
                event[22], sequences, event[21], event)
        elif event[0] in ("yellow_card", "suspension", "steal",
                          "substitution"):
            if event[21] == Opponent.HOME:
                calculate_correct_phase_fl(
                    event[22], sequences, Opponent.AWAY, event)
            else:
                calculate_correct_phase_fl(
                    event[22], sequences, Opponent.HOME, event)
        elif (
            event[0] in ("seven_m_awarded", "shot_off_target",
                         "seven_m_missed", "shot_saved",
                         "shot_blocked", "technical_ball_fault",
                         "technical_rule_fault", "yellow_card")
        ):
            calculate_correct_phase_fl(
                event[22], sequences, event[21], event)
        elif event[0] == "timeout_over":
            event[22] = calculate_timeouts_over_fl(
                sequences, event, events)
    return events, sequences


def give_last_event_fl(events: List[Any], time: int) -> Any:
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
    event: dict[Any, Any]
    for event in events[::-1]:
        if event[22] < time:
            if event[0] not in [
                "suspension",
                "yellow_card",
                "red_card",
                "suspension_over",
            ]:
                return event
    return None


def calculate_correct_phase_fl(
    time: int, sequences: list[tuple[int, int, int]], team_ab: Opponent,
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
    phase: int
    start: int
    end: int
    for start, end, phase in sequences:
        if start <= time < end:
            break
    if ((phase in (1, 3)) and team_ab == Opponent.HOME) or (
        (phase in (2, 4)) and team_ab == Opponent.AWAY
    ):
        print("correct Phase")

    else:
        new_time = search_phase_fl(time, sequences, team_ab)
        if new_time is not None:
            event[22] = new_time
            return event
    return event


def search_phase_fl(time: int,
                    sequences: list[tuple[int, int, int]], competitor: Opponent
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
            if (phase in (1, 3)) and competitor == Opponent.HOME:
                return end - 1  # Return the end of this phase
            if (phase in (2, 4)) and competitor == Opponent.AWAY:
                return end - 1  # Return the end of this phase for
    raise ValueError("No valid phase found for the given time!")


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
                          team_ab: Opponent, event: dict[Any, Any]
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

    if event[0] == "timeout":
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
        if ((phase_timeout in (1, 3) and (team_ab == Opponent.HOME))
                or (phase_timeout in (2, 4) and team_ab == Opponent.AWAY)):
            if int(time) == int(end - 1):
                print("correct Phase")
                return time
            return end - 1
        # Go through sequences in reverse to find the last matching phase
        # before `time`
        for _, end, phase in reversed(sequences):
            if end <= time:
                if (phase in (1, 3)) and (team_ab == Opponent.HOME):
                    return end - 1
                if (phase in (2, 4)) and (team_ab == Opponent.AWAY):
                    return end - 1
    raise ValueError("No valid phase found for timeout event!")


def calculate_timeouts_over_fl(sequences: list[tuple[int, int, int]],
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

    if event[0] == "timeout_over":
        time: int
        time = event[22]
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
            lastevent = give_last_event_fl(events, time)
            if lastevent[0] == "timeout":
                return time
            raise ValueError("Events are in wrong order!")
        time_inactive = calculate_inactive_phase_fl(time, sequences)
        if time_inactive is not None:
            lastevent = give_last_event_fl(events, time_inactive)
            if lastevent[0] == "timeout":
                return time_inactive
    raise ValueError("No valid phase found for timeout_over event!")


plot_phases(23400263, Approach.RULE_BASED)
