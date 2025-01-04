from datetime import datetime
from datetime import datetime as dt
from typing import Any

import pandas as pd
import pytz  # type: ignore
from floodlight import Code, Events
from floodlight.io.sportradar import read_event_data_json

import help_functions
import help_functions.reformatjson_methods


def createEventObjects(
        path_timeline: str,
        fps: float) -> tuple[Events, Events]:
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

    events = read_event_data_json(path_timeline)

    # Flatten the nested dictionary
    home_team_df, away_team_df = flatten_nested_events(events)

    # Create the Events objects for each group
    event_home = Events(events=home_team_df)
    event_away = Events(events=away_team_df)

    event_home.add_frameclock(fps)
    event_away.add_frameclock(fps)

    return event_home, event_away


def flatten_nested_events(nested_events: dict[Any, Any]
                          ) -> tuple[Any, Any]:
    home_team_events = []
    away_team_events = []

    for segment, teams in nested_events.items():
        for team, events_obj in teams.items():
            df = events_obj.events
            df['segment'] = segment
            df['team'] = team

            # Split into home, away, and unassigned
            if team == 'Home':
                home_team_events.append(df)
            elif team == 'Away':
                away_team_events.append(df)

    # Combine all DataFrames into one
    home_team_df = (pd.concat(
        home_team_events, ignore_index=True)
        if home_team_events else pd.DataFrame())
    away_team_df = (pd.concat(
        away_team_events, ignore_index=True)
        if away_team_events else pd.DataFrame())

    return home_team_df, away_team_df


def calculateOffset(offset_fr: int,
                    fps: float,
                    first_event_time_str: str,
                    offseth2_fr: int,
                    second_half: bool,
                    first_timestamp_pos: str,
                    first_vh2: int,
                    pos_fps: float) -> float:
    """
    Calculates the offset between positions data and event data.
    It is based on the real timestamps from eventdata and positional data.
    And the offset to the videodata is used to calcualte the offset.
    Args:
        offset_fr (int): The initial offset in frames.
        fps (int): Frames per second of the video.
        first_event_time_str (str): The timestamp of the first event in
        ISO format.
        offseth2_fr (int): The offset in frames for the second half.
        second_half (bool): Flag indicating if the event is in the second half.
        first_timestamp_pos (str): The first timestamp position in ISO format.
        first_vh2 (int): The first video half 2 position.
        pos_fps (int): Frames per second of the position data.
    Returns:
        float: The synchronized time position in frames.
    """
    utc_timezone = pytz.utc
    first_event_time = datetime.fromisoformat(
        first_event_time_str).replace(tzinfo=utc_timezone)
    if isinstance(first_timestamp_pos, tuple):
        first_timestamp = first_timestamp_pos[0]
    else:
        first_timestamp_str = str(first_timestamp_pos)
    first_timestamp = datetime.fromisoformat(first_timestamp_str).replace(
        tzinfo=utc_timezone
    )

    delta = first_event_time - first_timestamp
    delta_fr = delta.seconds * fps

    synced_time = delta_fr + offset_fr
    if second_half:
        synced_time = synced_time + offseth2_fr

    synced_time_pos_fr = (synced_time/fps) * pos_fps
    return synced_time_pos_fr


def run(match_id: int) -> tuple[Code, Code]:
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
        _, path_timeline, _, positions_path, cut_h1, offset_h2,
        first_vh2, _
    ) = help_functions.reformatjson_methods.get_paths_by_match_id(match_id)
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = help_functions.reformatjson_methods.load_first_timestamp_position(
        positions_path)

    # Framerate of the video
    fps_video = 29.97
    # Load event data and adjust timestamps
    event_home, event_away = createEventObjects(path_timeline,
                                                fps_positional)
    # first_time_stamp_event: pd.Timestamp
    # Match start timestamp
    first_time_stamp_event = event_home.events['time_stamp'][0]
    first_time_stamp_event = first_time_stamp_event.strftime(
        '%Y-%m-%d %H:%M:%S')
    print("match_start_datetime:", first_time_stamp_event)

    # timezone
    utc_timezone = pytz.utc

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_date = dt.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=utc_timezone)
    print("positional_data_start_date:", positional_data_start_date)
    offset = calculateOffset(cut_h1, fps_video, first_time_stamp_event,
                             offset_h2, False, first_time_pos_str,
                             first_vh2, fps_positional)
    event_home.events['frameclock'] = event_home.events['frameclock'] + offset
    event_stream_home = event_home.get_event_stream(fade=1)
    event_stream_away = event_away.get_event_stream(fade=1)
    # Change the time of the events to the timeframe of the positional data
    return event_stream_home, event_stream_away


event_stream_home, event_stream_away = run(23400263)
print(event_stream_home)
print(event_stream_away)
