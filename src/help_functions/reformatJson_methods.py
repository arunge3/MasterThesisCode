import json
import os
from datetime import datetime, timezone
from typing import Any, Optional, Union

import pandas as pd
import pytz  # type: ignore
from floodlight.io.kinexon import get_meta_data

"""
This module provides functions to handle and reformat JSON data related
to handball match events.
Functions:
    load_first_timestamp_and_offset(file_path)
    synchronize_time(event_time_str, second_half, first_timestamp_str,
    offset_fr, offseth2_fr, first_vh2, fps)
    get_paths_by_match_id(match_id)
    reformatJson(path_timeline, path_output_jsonl, first_timestamp_ms,
    offset, offset_h2, first_vh2, fps)
"""


def load_first_timestamp_position(file_path: str) -> tuple[str, Any, Any]:
    """
    Loads the first timestamp from a CSV file and converts it to a
    formatted date-time string.
    Args:
        file_path (str): The path to the CSV file containing the
        timestamp data.
    Returns:
        str: The first timestamp in the CSV file, formatted as a
        date-time string in UTC.
    """

    _, _, framerate, t_null_pos = get_meta_data(file_path)

    date_time = (datetime.fromtimestamp((t_null_pos / 1000),
                 tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    print("First Time Stamp Positional Data:", date_time)
    return date_time, t_null_pos, framerate


def synchronize_time(
    event_time_str: str,
    second_half: bool,
    first_timestamp_opt: Optional[Union[str, tuple[Any]]],
    offset_fr: int,
    offseth2_fr: int,
    first_vh2: int,
    fps: int,
) -> int:
    """
    Synchronizes the event time with the first timestamp and calculates
    the synchronized time in frames.
    Args:
        event_time_str (str): The event time as an ISO formatted string.
        second_half (bool): A flag indicating if the event is in the second
        half.
        first_timestamp_str (str): The first timestamp as an ISO formatted
        string.
        offset_fr (int): The offset in frames for the first half.
        offseth2_fr (int): The offset in frames for the second half.
        first_vh2 (int): The first value for the second half
        (not used in the function).
        fps (int): Frames per second.
    Returns:
        int: The synchronized time in frames.
    """
    utc_timezone = pytz.utc
    first_timestamp_str: str
    event_time = datetime.fromisoformat(
        event_time_str).replace(tzinfo=utc_timezone)
    if isinstance(first_timestamp_opt, tuple):
        first_timestamp_str = first_timestamp_opt[0]
    else:
        first_timestamp_str = str(first_timestamp_opt)
    first_timestamp = datetime.fromisoformat(first_timestamp_str).replace(
        tzinfo=utc_timezone
    )

    delta = event_time - first_timestamp
    delta_fr = delta.seconds * fps

    synced_time = delta_fr + offset_fr
    if second_half:
        synced_time = synced_time + offseth2_fr
    return synced_time


def get_paths_by_match_id(
    match_id: int,
    video_base_path: str = r"D:\Handball\HBL_Videos\season_2021",
    annotation_base_path: str = (
        r"D:\Handball\HBL_Events\season_20_21\EventTimeline"),
    output_base_path: str = r"D:\Handball\HBL_Synchronization\Annotationen",
    position_base_path: str = r"D:\Handball\HBL_Positions\20-21",
    csv_file: str = r"D:\Handball\HBL_Synchronization\mapping20_21.csv",
    lookup_file: str = (
        r"D:\Handball\HBL_Events\lookup\lookup_matches_20_21.csv")
) -> tuple[
    Optional[str], Optional[str], Optional[str], Optional[str],
    Optional[str], Optional[str], Optional[str], Optional[str]
]:
    """
    Retrieves various file paths and metadata associated with a given match ID.
    Args:
        match_id (int): The ID of the match to retrieve paths for.
        video_base_path (str): Base path for the video files.
        annotation_base_path (str): Base path for the annotation files.
        output_base_path (str): Base path for the output files.
        position_base_path (str): Base path for the position files.
    Returns:
        tuple: A tuple containing the following elements:
            - video_path (str or None): Path to the raw video file.
            - annotation_path (str or None): Path to the annotation JSON file.
            - output_path (str or None): Path to the reformatted JSONL output
            file.
            - file_path_position (str or None): Path to the position file.
            - cut_h1 (str or None): Metadata for the first half cut.
            - offset_h2 (str or None): Metadata for the second half offset.
            - first_vh2 (str or None): Metadata for the first video of the
            second half.
            - matchname (str or None): Name of the match.
    Returns None for all elements if the match ID is not found in the
    CSV files.
    """
    df = pd.read_csv(csv_file, delimiter=";")
    match_row = df[df["match_id"] == int(match_id)]

    if match_row.empty:
        return None, None, None, None, None, None, None, None

    video_file = match_row.iloc[0]["raw_video"]
    annotation_file = f"sport_events_{match_id}_timeline.json"
    output_file = f"sport_events_{match_id}_timeline_reformatted.jsonl"

    video_path = os.path.join(video_base_path, video_file)
    annotation_path = os.path.join(annotation_base_path, annotation_file)
    output_path = os.path.join(output_base_path, output_file)
    match_name = match_row.iloc[0]["raw_pos_knx"]

    lookup_df = pd.read_csv(lookup_file)
    lookup_row = lookup_df[lookup_df["match_id"]
                           == f"sr:sport_event:{match_id}"]
    if lookup_row.empty:
        return None, None, None, None, None, None, None, None

    file_name_position = lookup_row.iloc[0]["file_name"]

    file_path_position = os.path.join(position_base_path, file_name_position)

    cut_h1 = match_row.iloc[0]["cutH1"]
    offset_h2 = match_row.iloc[0]["offset_h2"]
    first_vh2 = match_row.iloc[0]["firstVH2"]

    return (
        video_path,
        annotation_path,
        output_path,
        file_path_position,
        cut_h1,
        offset_h2,
        first_vh2,
        match_name,
    )


def getFirstTimeStampEvent(path_timeline: str) -> Optional[str]:
    """
    Extracts the timestamp of the first "match_started" event from
    a JSON timeline file.
    Args:
        path_timeline (str): The file path to the JSON timeline.
    Returns:
        str or None: The timestamp of the first "match_started"
        event if found, otherwise None.
    """

    with open(path_timeline, "r") as file:
        data = json.load(file)
    events = data.get("timeline", [])
    for event in events:
        if event.get("type") == "match_started":
            return str(event.get("time"))
    return None


# def calculateOffset(
#         first_event_time_str: str,
#         first_timestamp_pos: int,
#         fps_vid: int,
#         fps_pos: int,
#         offset_fr: int,
#         second_half: bool,
#         offseth2_fr: int) -> int:
#     """
#     Information why I did the synchronisation like this:
#     Das Event "matched_started" inklusive Zeitstempel wird verwendet,
#     Anschließend wird noch das erste Event aus der Positional
#     Data genommen und dessen Zeitstempel. Von diesen beiden
#     wird der Unterschied berechnet. Der UNterschied wird in
#     sekunden angegeben. Im Video sind das 29.97 Frames pro Sekunde,
#     in der Positional Data 20 Frames pro Sekunde. Das bedeuted,
#     dass 1 Sekunde in der Positional Data 1.5 Sekunden im Video sind.
#     Somit wird der Unterschied in Sekunden mit der Frame Rate des
#     Videos multipliziert und der Offset der Positional Data addiert.
#     Damit der Unterschied zwischen den Framerates noch beglichen
#     werden kann wird die Framerate der Positional Data mit dem Unterschied
#     multipliziert abgezogen.

#     Args:
#         first_event_time_str (_type_): _description_
#         first_timestamp_pos (_type_): _description_
#         fps_vid (_type_): _description_
#         fps_pos (_type_): _description_
#         offset_fr (_type_): _description_
#         second_half (_type_): _description_
#         offseth2_fr (_type_): _description_

#     Returns:
#         _type_: _description_
#     """
#     first_timestamp_pos_date: datetime
#     synced_time: int
#     utc_timezone = pytz.utc
#     first_event_time = (datetime.fromisoformat(
#         first_event_time_str).replace(tzinfo=utc_timezone))
#     first_timestamp_pos_date = datetime.fromtimestamp(
#         (first_timestamp_pos / 1000), tz=timezone.utc
#     )

#     delta = first_event_time - first_timestamp_pos_date
#     delta_fr_pos = delta.seconds * fps_pos
#     synced_time = delta_fr_pos + offset_fr - delta_fr_pos
#     if second_half:
#         synced_time = synced_time + offseth2_fr
#     return synced_time


def reformatJson(
        path_timeline: str,
        path_output_jsonl: str,
        first_timestamp_ms: Optional[Union[str, tuple[Any]]],
        offset: int,
        offset_h2: int,
        first_vh2: int,
        fps: int) -> None:
    """
    Reformats a JSON timeline of events into a JSONL file with specific event
    details.
    Args:
        path_timeline (str): Path to the input JSON file containing the
        timeline of events.
        path_output_jsonl (str): Path to the output JSONL file where
        reformatted events will be written.
        first_timestamp_ms (int): The first timestamp in milliseconds.
        offset (int): Offset value for time synchronization.
        offset_h2 (int): Offset value for the second half of the game.
        first_vh2 (int): First value for the second half.
        fps (int): Frames per second for time synchronization.
    Returns:
        None
    """

    with open(path_timeline, "r") as file:
        data = json.load(file)

    events = data.get("timeline", [])

    with open(path_output_jsonl, "w") as file:
        for event in events:
            competitor = event.get("competitor", None)
            type = event.get("type")
            id = event.get("id")
            match_clock = event.get("match_clock", None)
            ball_possession = {"home": "A", "away": "B",
                               "None": "none"}.get(competitor, "")

            if type == "score_change":
                pass_handball = ""
                shot = "successful"
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = "kick-off"
                referee_decision = "goal"
            elif type == "yellow_card":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = "yellow"
            elif type == "red_card":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = "red"
            elif type == "suspension":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = "two min"
            elif type == "seven_m_awarded":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = "penalty"
                ball_reception = ""
                static_ball_action = "penalty"
                referee_decision = "7m"
            elif type == "seven_m_missed":
                pass_handball = ""
                shot = "saved"
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = "penalty"
                referee_decision = ""
            elif type == "break_start":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "period_score":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "period_start":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = "kick-off"
                referee_decision = ""
                period_name = event.get("period_name", None)
            elif type == "shot_off_target":
                pass_handball = ""
                shot = "off target"
                unintentional_ball_release = "other"
                ball_reception = ""
                static_ball_action = "throw-in"
                referee_decision = "out of field"
            elif type == "shot_blocked":
                pass_handball = ""
                shot = "blocked/intercepted"
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "shot_saved":
                pass_handball = ""
                shot = "saved"
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "steal":
                pass_handball = "intercepted"
                shot = ""
                unintentional_ball_release = "successful interference"
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "suspension_over":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "technical_rule_fault":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = "other"
                ball_reception = ""
                static_ball_action = "free-throw"
                referee_decision = "other"
            elif type == "technical_ball_fault":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = "other"
                ball_reception = ""
                static_ball_action = "free-throw"
                referee_decision = "other"
            elif type == "substitution":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "timeout":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            elif type == "timeout_over":
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            else:
                pass_handball = ""
                shot = ""
                unintentional_ball_release = ""
                ball_reception = ""
                static_ball_action = ""
                referee_decision = ""
            second_half = False
            if match_clock is not None:
                match_minutes, match_seconds = map(int, match_clock.split(":"))
                threshold_minutes = 30
                threshold_seconds = 0
                if (match_minutes > threshold_minutes) or (
                    match_minutes == threshold_minutes
                    and match_seconds > threshold_seconds
                ):
                    second_half = True
            if type == "period_start" and period_name == "2nd Half":
                second_half = True

            reformatted_event = {
                "t_start": int(
                    synchronize_time(
                        event.get("time", None),
                        second_half,
                        first_timestamp_ms,
                        offset,
                        offset_h2,
                        first_vh2,
                        fps,
                    )
                ),
                "t_end": "-1",
                "annotator": "id: " + str(id),
                "labels": {
                    "type": type,
                    "pass": pass_handball,
                    "shot": shot,
                    "unintentional ball release": unintentional_ball_release,
                    "ball reception": ball_reception,
                    "static ball action": static_ball_action,
                    "referee decision": referee_decision,
                    "ball possession": ball_possession,
                },
            }
            file.write(json.dumps(reformatted_event) + "\n")


def reformatJson_Time_only(
    path_timeline: str,
    first_timestamp_ms: int,
    offset: int,
    offset_h2: int,
    first_vh2: int,
    fps: int,
) -> dict[Any, Any]:
    """
    Reformats the timestamps in a JSON timeline file.
    Args:
        path_timeline (str): The path to the JSON file containing the
        timeline data.
        first_timestamp_ms (int): The first timestamp in milliseconds.
        offset (int): The offset to be applied to the timestamps.
        offset_h2 (int): The offset to be applied to the timestamps
        in the second half.
        first_vh2 (int): The first timestamp of the second half in
        milliseconds.
        fps (int): Frames per second, used for time synchronization.
    Returns:
        dict: The modified timeline data with updated timestamps.
    """
    data: dict[Any, Any]
    with open(path_timeline, "r") as file:
        data = json.load(file)

    events = data.get("timeline", [])
    # Loop through the entries and change their timestamps
    for event in events:
        type = event.get("type")
        match_clock = event.get("match_clock", None)
        second_half = False
        if type == "period_start":
            period_name = event.get("period_name", None)
        else:
            period_name = None
        if match_clock is not None:
            match_minutes, match_seconds = map(int, match_clock.split(":"))
            threshold_minutes = 30
            threshold_seconds = 0
            if ((match_minutes > threshold_minutes) or
                    (match_minutes == (threshold_minutes and
                                       match_seconds > threshold_seconds))):
                second_half = True
            elif type == "period_start" and period_name == "2nd Half":
                second_half = True
        event["time"] = int(
            synchronize_time(
                event.get("time", None),
                second_half,
                str(first_timestamp_ms),
                offset,
                offset_h2,
                first_vh2,
                fps,
            )
        )

    return data
