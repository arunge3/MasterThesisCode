"""
This script demonstrates various functionalities of the `os` module
for interacting with the operating system.
"""

import json
import os
from datetime import datetime as dt
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import matplotlib
import numpy as np
import pandas as pd
import pytz  # type: ignore
from floodlight import Events
from floodlight.io.sportradar import read_event_data_json
from matplotlib import pyplot as plt

import cost_function_approach
import cost_function_approach_2
import help_functions
import help_functions.pos_data_approach
import help_functions.reformatjson_methods
import sport_analysis
import variables.data_variables as dv
from plot_functions import processing
from plot_functions.plot_phases import berechne_phase_und_speichern_fl

matplotlib.use("TkAgg", force=True)


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
        by=event_all.events.columns[2])

    # Create a filtered list for timeout and timeout_over
    filtered_test = []
    team = None

    for _, row in event_all.events.iterrows():
        if row.iloc[0] == "timeout":
            team = row.iloc[21]  # Store the team for the last timeout
        elif row.iloc[0] == "timeout_over" and row.iloc[21] != team:
            continue  # Skip this timeout_over if it doesn't match the team
        else:
            team = None
        filtered_test.append(row)

    # Create a new DataFrame from the filtered rows
    event_all.events = pd.DataFrame(
        filtered_test, columns=event_all.events.columns)

    return event_all


def map_ids_to_dataframe(json_timeline: dict[Any, Any],
                         dataframe: Events) -> Events:
    """
    Maps event IDs from a JSON timeline to a DataFrame of events.
    This function takes a JSON timeline and a DataFrame of events,
    and maps the event IDs from the JSON timeline to the
    corresponding events in the DataFrame based on matching event
    types, timestamps, and optionally competitors.
    Args:
        json_timeline (dict[Any, Any]): A dictionary representing
        the JSON timeline where each event contains keys such as
        "type", "time", "competitor", and "id".
        dataframe (Events): An Events object containing a DataFrame
        of events with columns such as "eID", "time_stamp", and
        "team".
    Returns:
        Events: The updated Events object with the 'eventID' column
        populated based on the matching criteria.
    """

    # Initialize a new column 'eventID' in the events DataFrame
    dataframe.events['eventID'] = None
    for idx, event_df in dataframe.events.iterrows():
        for event in json_timeline:
            # Replace 'type' with the actual column name
            if event.get("type") != event_df["eID"]:
                continue
            if (event.get("time") is not None and
                    pd.Timestamp(event.get("time")) ==
                    event_df["time_stamp"]):
                if event.get("competitor") is not None:
                    # Replace with actual column
                    if event.get("competitor") == event_df["team"].value:
                        # Update the 'eventID' column in the DataFrame
                        dataframe.events.at[idx,
                                            "eventID"] = event.get("id")
                        break
                else:
                    dataframe.events.at[idx, "eventID"] = event.get("id")
                    break

    return dataframe


def add_event_time_framerate(dataframe: pd.DataFrame, first_timestamp_ms: str,
                             fps: float) -> pd.DataFrame:
    """
    Adds a new column to the DataFrame with the event time in frames.
    """
    dataframe['event_time_framerate'] = None
    for idx, row in dataframe.iterrows():
        event_time = row['time_stamp']
        event_time_framerate = (help_functions.reformatjson_methods.
                                synchronize_time(
                                    event_time, first_timestamp_ms, fps))

        dataframe.at[idx, 'event_time_framerate'] = event_time_framerate

    return dataframe


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
                df['team'] = dv.Opponent.HOME
            elif team == "Away":
                df['team'] = dv.Opponent.AWAY
            else:
                df['team'] = dv.Opponent.NONE

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
    if not isinstance(path_timeline, (str, Path)):
        raise ValueError(f"Invalid path: {path_timeline}")
    path_timeline = Path(path_timeline)
    data = json.loads(path_timeline.read_text(encoding='utf-8'))
    df_events = data.get("timeline", [])
    # Match start timestamp
    first_time_stamp_event = event_all.events['time_stamp'][0]
    first_time_stamp_event = first_time_stamp_event.strftime(
        '%Y-%m-%d %H:%M:%S')

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_timestamp = dt.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=pytz.utc)
    offset = calculate_offset(first_time_stamp_event,
                              first_time_pos_str,
                              fps_positional)
    event_all.events['frameclock'] = event_all.events['frameclock'] + offset
    event_all = map_ids_to_dataframe(df_events, event_all)
    event_all.events = add_event_time_framerate(
        event_all.events, first_time_pos_str, fps_positional)
    event_stream_all = event_all.get_event_stream(fade=1)

    return event_stream_all, offset, event_all.events


def approach_plot(match_id: int, approach: dv.Approach
                  = dv.Approach.RULE_BASED,
                  base_path: str = r"D:\Handball\HBL_Events\season_20_21"
                  ) -> None:
    """
    Plots the phases of a handball match along with event markers.
    """
    (events, sequences, datei_pfad) = (handle_approach(
        approach, processing.calculate_sequences(match_id),
        match_id, os.path.join(base_path, r"Datengrundlagen")))
    plot_phases(events, sequences, datei_pfad, match_id, approach)
    if approach == dv.Approach.COST_BASED:

        events1, sequences = correct_events_fl(events, sequences)
        datei_pfad = os.path.join(os.path.join(base_path, r"Datengrundlagen"),
                                  r"cost_based_cor",
                                  (str(match_id) + "_cost_based_cor_fl.csv"))
        plot_phases(events1, sequences, datei_pfad, match_id, approach)
        events2, sequences = synchronize_events_fl_rule_based(
            events, sequences)
        datei_pfad = os.path.join(os.path.join(base_path, r"Datengrundlagen"),
                                  r"cost_based_rb",
                                  (str(match_id) + "_cost_based_rb_fl.csv"))
        plot_phases(events2, sequences, datei_pfad, match_id, approach)


def plot_phases(events: Any, sequences: list[tuple[int, int, int]],
                datei_pfad: str, match_id: int, approach: dv.Approach
                = dv.Approach.RULE_BASED,
                base_path: str = r"D:\Handball\HBL_Events\season_20_21"
                ) -> None:
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
    # if approach == dv.Approach.COST_BASED:
    #     (events, sequences, datei_pfad) = (handle_approach(
    #     approach, processing.calculate_sequences(match_id),
    #     match_id, os.path.join(base_path, r"Datengrundlagen")))

    # else:
    #     (events, sequences, datei_pfad) = (handle_approach(
    #         approach, processing.calculate_sequences(match_id),
    #         match_id, os.path.join(base_path, r"Datengrundlagen")))
    analysis_results = sport_analysis.analyze_events_and_formations(
        events, match_id)
    # print(analysis_results)
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
    # Save analysis results to a JSON file
    analysis_results_path = os.path.join(
        base_path, f"analysis_results_{match_id}_{approach.name}.json")
    with open(analysis_results_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=4)
    berechne_phase_und_speichern_fl(events, sequences, datei_pfad)
    # Add event markers with labels from `type`
    if hasattr(events, 'values'):
        for event in events.values:
            # Find the y value on the continuous line for this event's time
            event_y = None
            for start, end, phase in sequences:
                if start <= event[24] < end:
                    event_y = phase_positions[phase]

                    break
            if event_y is not None:
                ax.plot(
                    event[24],
                    event_y,
                    "x",
                    color=event_colors.get(event[0], event_colors["default"]),
                    markersize=8,
                    label=event[0] if event[0] not in added_labels else "",
                )
                added_labels.add(event[0])
        # Add legend
        ax.legend(title="Event Types", loc="upper right",
                  bbox_to_anchor=(1.15, 1))

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
        # plt.show()
    else:
        for event in events:
            # Find the y value on the continuous line for this event's time
            event_y = None
            for start, end, phase in sequences:

                if start <= event["time"] < end:
                    event_y = phase_positions[phase]

                    break
            if event_y is not None:
                ax.plot(
                    event["time"],
                    event_y,
                    "x",
                    color=event_colors.get(
                        event["type"], event_colors["default"]),
                    markersize=8,
                    label=(event["type"] if event["type"]
                           not in added_labels else ""),
                )
                added_labels.add(event["type"])
        # Add legend
        ax.legend(title="Event Types", loc="upper right",
                  bbox_to_anchor=(1.15, 1))

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
        # plt.show()


def handle_approach(approach: dv.Approach,
                    sequences: list[tuple[int, int, int]],
                    match_id: int, datengrundlage: str) -> (
                        tuple[Any, list[tuple[int, int, int]], str]):
    """
    Handles the approach for the event stream.
    Args:

        approach (dv.Approach): The approach to use for
        synchronization
        sequences (list[tuple[int, int, int]]): The sequences
        to use for synchronization
        match_id (int): The match ID to use for synchronization
        datengrundlage (str): The base path to the data files
    Returns:
        tuple[Any, list[tuple[int, int, int]], str]: A tuple
        containing the events,
        the sequences, and the datei_pfad.
    """
    if approach == dv.Approach.RULE_BASED:
        (_, _, events) = calculate_event_stream(match_id)
        # print(events)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events, sequences = synchronize_events_fl_rule_based(
            events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"rulebased",
                                  (str(match_id) + "_rb_fl.csv"))
    elif approach == dv.Approach.POS_DATA:
        (_, _, events) = calculate_event_stream(match_id)
        datei_pfad = os.path.join(datengrundlage, r"pos",
                                  (str(match_id) + "_pos_fl.csv"))
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = help_functions.pos_data_approach.sync_event_data_pos_data(
            events, match_id)
    elif approach == dv.Approach.BASELINE:
        (_, _, events) = calculate_event_stream(match_id)
        events = adjust_timestamp_baseline(events)

        datei_pfad = os.path.join(datengrundlage, r"baseline",
                                  (str(match_id) + "_bl_fl.csv"))
    elif approach == dv.Approach.NONE:
        (_, _, events) = calculate_event_stream(match_id)
        datei_pfad = os.path.join(
            datengrundlage, r"none", (str(match_id) + "_none_fl.csv"))
    elif approach == dv.Approach.POS_RB:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = help_functions.pos_data_approach.sync_event_data_pos_data(
            events, match_id)

        events, sequences = synchronize_events_fl_rule_based(
            events, sequences)
        datei_pfad = os.path.join(datengrundlage, r"pos_rb",
                                  (str(match_id) + "_pos_rb_fl.csv")
                                  )
    elif approach == dv.Approach.POS_CORRECTION:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = help_functions.pos_data_approach.sync_event_data_pos_data(
            events, match_id)
        events, sequences = correct_events_fl(events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"pos_cor",
                                  (str(match_id) + "_pos_cor_fl.csv"))
    elif approach == dv.Approach.COST_BASED:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = cost_function_approach_2.main(match_id, events)
        # events = cost_function_approach.sync_events_cost_function(
        #     events, sequences, match_id)

        datei_pfad = os.path.join(datengrundlage, r"cost_based",
                                  (str(match_id) + "_cost_based_fl.csv"))
    elif approach == dv.Approach.COST_BASED_COR:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = cost_function_approach.sync_events_cost_function(
            events, sequences, match_id)
        events, sequences = correct_events_fl(events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"cost_based_cor",
                                  (str(match_id) + "_cost_based_cor_fl.csv"))
    elif approach == dv.Approach.COST_BASED_RB:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)

        events = cost_function_approach.sync_events_cost_function(
            events, sequences, match_id)
        events, sequences = synchronize_events_fl_rule_based(
            events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"cost_based_rb",
                                  (str(match_id) + "_cost_based_rb_fl.csv"))
    else:
        raise ValueError("Invalid approach specified!")
    return events, sequences, datei_pfad


def adjust_timestamp_baseline(events: Any) -> Any:
    """
    Adjusts the timestamp of the events to the baseline.
    """
    event_adjustments = {
        'break_start': -359,
        'match_started': -258983,
        'red_card': -260,
        'score_change': -109,
        'seven_m_awarded': -469,
        'seven_m_missed': -74,
        'shot_blocked': -142,
        'shot_off_target': -237,
        'shot_saved': -251,
        'steal': -257,
        'substitution ': -5,
        'suspension': -386,
        'suspension_over': -384,
        'technical_ball_fault': -245,
        'technical_rule_fault': -258,
        'timeout': -284,
        'timeout_over': -29,
        'yellow_card': -268
    }
    for idx, event in enumerate(events.values):
        event_type = event[0]
    # Dictionary mapping event types to their mean values (rounded)

    # Get the event type and adjust timestamp based on mean value
        event_type = event[0]
        if event_type in event_adjustments:
            mean_adjustment = event_adjustments[event_type]
            events.iloc[idx, 24] = events.iloc[idx, 24] + mean_adjustment
    return events


def add_team_to_events(events: pd.DataFrame,
                       team_order: list[str]) -> pd.DataFrame:
    """
    Fügt die Team-Information zu den Ereignissen hinzu.

    Args:
        events: Die Event-Daten
        team_order: Die Reihenfolge der Teams
    Returns:
        Die Event-Daten mit der Team-Information
    """
    # Add new column for team if it doesn't exist
    if 'teamAB' not in events.columns:
        events['teamAB'] = None

    for idx, event in enumerate(events.values):
        if event[10] is not None:
            # Add team A/B designation based on team_order index
            if event[10] == team_order[0]:
                events.iloc[idx, 25] = dv.Team.A
            elif event[10] == team_order[1]:
                events.iloc[idx, 25] = dv.Team.B
    return events


def calculate_team_order(events: Any) -> list[str]:
    """
    Berechnet die Reihenfolge der Teams basierend auf den Ereignissen.

    Args:
        events: Die Event-Daten
    Returns:
        Liste der Teams in der Reihenfolge der Ereignisse
    """
    team_order = []
    for event in events.values:
        if event[10] is not None:
            if event[10] not in team_order:
                team_order.append(event[10])
    # Sort team order alphabetically
    team_order.sort()
    return team_order


def correct_events_fl(events: Any, sequences: list[tuple[int, int, int]]
                      ) -> tuple[Any, list[tuple[int, int, int]]]:
    """
    Korrigiert ML-basierte Event-Synchronisation mit Floodlight-Daten.

    Args:
        events: Die Event-Daten
        sequences: Liste von Sequenzen (start, end, phase)
    Returns:
        Tuple aus korrigierten Events und Sequenzen
    """
    for idx, event in enumerate(events.values):
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            events.iloc[idx, 24] = search_phase_ml_fl(
                event[24], sequences, event[25])
    return events, sequences


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
    """
    return calculate_timeouts_fl(event.values[24], sequences,
                                 event.values[25], event)


def handle_timeout_over(event: dict[Any, Any],
                        sequences: list[tuple[int, int, int]],
                        events: list[Any]
                        ) -> int:
    """
    Handles timeout over events by calculating the appropriate
    phase after a timeout ends.


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
    Sucht nach der passenden Phase für einen Competitor, prüft zuerst
    die aktuelle Phase, dann die nächste und schließlich die vorherigen
    Phasen.


    Args:
        time (int): Der Zeitpunkt für den die Phase gesucht wird
        sequences (list): Liste von Sequenzen (start, end, phase)
        competitor (dv.Opponent): Der zu prüfende Competitor (HOME/AWAY)

    Returns:
        int: Zeitpunkt in der passenden Phase

    Raises:
        ValueError: Wenn keine passende Phase gefunden wurde
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
            # TODO Ich möchte berechnen dass das letzte Event
            # das Timeout war und das in der Zeit dazwischen
            # nur inaktive phase war
            # TODO ist noch flasch gibt das flasche event zurück
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
