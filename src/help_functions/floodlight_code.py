"""
This module contains various functions and classes used for processing and
analyzing handball match data. It includes functions for creating event
objects, evaluating player performance, synchronizing events, and plotting
phases of the match. The module relies on several external libraries such as
numpy, pandas, matplotlib, and floodlight, as well as custom modules for
specific approaches and data handling.

Key functionalities provided by this module include:
- Creating event streams from timeline files.
- Evaluating player performance on the field.
- Synchronizing events based on different rules.
- Plotting phases of the match with event markers.
- Handling different approaches for data analysis and correction.

The module is designed to work with handball match data and provides tools for
comprehensive analysis and visualization of match events and phases.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""


import json
from datetime import datetime as dt
from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd
import pytz  # type: ignore
from floodlight import Events
from floodlight.io.sportradar import read_event_data_json

import preprocessing.reformatJson_methods as reformatjson_methods
import variables.data_variables as dv

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
    Args:
        dataframe (pd.DataFrame): The DataFrame to add the event time to.
        first_timestamp_ms (str): The first timestamp in milliseconds.
        fps (float): The frames per second.
    Returns:
        pd.DataFrame: The DataFrame with the event time in frames.
    """
    dataframe['event_time_framerate'] = None
    for idx, row in dataframe.iterrows():
        event_time = row['time_stamp']
        event_time_framerate = (reformatjson_methods.
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
    ) = reformatjson_methods.get_paths_by_match_id(match_id)
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = reformatjson_methods.load_first_timestamp_position(
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


def adjust_timestamp_baseline(events: Any) -> Any:
    """
    Adjusts the timestamp of the events to the baseline.
    Args:
        events: The event data
    Returns:
        The event data with the adjusted timestamp
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
    Adds the team information to the events.

    Args:
        events: The event data
        team_order: The order of teams
    Returns:
        The event data with the team information
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
    Calculates the order of teams based on the events.

    Args:
        events: The event data
    Returns:
        List of teams in the order of events
    """
    team_order = []
    for event in events.values:
        if event[10] is not None:
            if event[10] not in team_order:
                team_order.append(event[10])
    # Sort team order alphabetically
    team_order.sort()
    return team_order
