"""
This script processes and reformats JSON timeline data for handball matches. It includes functions to load timestamps, 
synchronize event times, retrieve file paths based on match IDs, and reformat JSON data into JSONL format.
Functions:
    load_first_timestamp_and_offset(file_path):
    synchronize_time(event_time_str, second_half, first_timestamp_str, offset_fr, offseth2_fr, first_vh2, fps):
    get_paths_by_match_id(match_id):
    reformatJson(path_timeline, path_output_jsonl, first_timestamp_ms, offset, offset_h2, first_vh2, fps):
Variables:
    fps (float): Frames per second for time synchronization.
    match_id (int): The ID of the match to process.
    video_path (str): Path to the raw video file.
    path_timeline (str): Path to the annotation JSON file.
    path_output_jsonl (str): Path to the reformatted JSONL output file.
    file_path_position (str): Path to the position file.
    cut_h1 (str): Metadata for the first half cut.
    offset_h2 (str): Metadata for the second half offset.
    first_vh2 (str): Metadata for the first video of the second half.
    first_timestamp_ms (str): The first timestamp in milliseconds.
"""
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import pytz

def load_first_timestamp_and_offset(file_path):
    """
    Loads the first timestamp from a CSV file and converts it to a formatted date-time string.
    Args:
        file_path (str): The path to the CSV file containing the timestamp data.
    Returns:
        str: The first timestamp in the CSV file, formatted as a date-time string in UTC.
    """
    
    df = pd.read_csv(file_path)
    first_timestamp_ms = df['ts in ms'].iloc[0]
    unix_timestamp = first_timestamp_ms / 1000  
    date_time = str(datetime.fromtimestamp(unix_timestamp,  tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
    
    return date_time


def synchronize_time(event_time_str, second_half, first_timestamp_str, offset_fr,offseth2_fr, first_vh2, fps):
    """
    Synchronizes the event time with the first timestamp and calculates the synchronized time in frames.
    Args:
        event_time_str (str): The event time as an ISO formatted string.
        second_half (bool): A flag indicating if the event is in the second half.
        first_timestamp_str (str): The first timestamp as an ISO formatted string.
        offset_fr (int): The offset in frames for the first half.
        offseth2_fr (int): The offset in frames for the second half.
        first_vh2 (int): The first value for the second half (not used in the function).
        fps (int): Frames per second.
    Returns:
        int: The synchronized time in frames.
    """
    utc_timezone = pytz.utc
    
    event_time = datetime.fromisoformat(event_time_str).replace(tzinfo=utc_timezone)
    first_timestamp = datetime.fromisoformat(first_timestamp_str).replace(tzinfo=utc_timezone)
    
    
    delta = event_time - first_timestamp
    delta_fr= delta.seconds*fps

    synced_time = delta_fr+ offset_fr
    if(second_half):
        synced_time = synced_time + offseth2_fr
    return synced_time

def get_paths_by_match_id(match_id):
    """
    Retrieves various file paths and metadata associated with a given match ID.
    Args:
        match_id (int): The ID of the match to retrieve paths for.
    Returns:
        tuple: A tuple containing the following elements:
            - video_path (str or None): Path to the raw video file.
            - annotation_path (str or None): Path to the annotation JSON file.
            - output_path (str or None): Path to the reformatted JSONL output file.
            - file_path_position (str or None): Path to the position file.
            - cut_h1 (str or None): Metadata for the first half cut.
            - offset_h2 (str or None): Metadata for the second half offset.
            - first_vh2 (str or None): Metadata for the first video of the second half.
    Returns None for all elements if the match ID is not found in the CSV files.
    """
    
    csv_file = r"D:\Handball\HBL_Synchronization\mapping20_21.csv"
    lookup_file = r"D:\Handball\HBL_Events\lookup\lookup_matches_20_21.csv"
    video_base_path = r"D:\Handball\HBL_Videos\season_2021"
    annotation_base_path = r"D:\Handball\HBL_Events\season_20_21\EventTimeline"
    output_base_path = r"D:\Handball\HBL_Events\season_20_21\EventJson"
    position_base_path = r"D:\Handball\HBL_Positions\20-21"
    
    df = pd.read_csv(csv_file, delimiter=';')
    match_row =  df[df['match_id'] == int(match_id)]
    
    if match_row.empty:
        return None, None, None,  None, None, None , None

    video_file = match_row.iloc[0]['raw_video']
    annotation_file = f"sport_events_{match_id}_timeline.json"
    output_file = f"sport_events_{match_id}_timeline_reformatted.jsonl"
    
    video_path = os.path.join(video_base_path, video_file)
    annotation_path = os.path.join(annotation_base_path, annotation_file)
    output_path = os.path.join(output_base_path, output_file)
    
    lookup_df = pd.read_csv(lookup_file)
    lookup_row = lookup_df[lookup_df['match_id'] == f"sr:sport_event:{match_id}"]
    if lookup_row.empty:
        return None, None, None, None, None, None, None

    file_name_position = lookup_row.iloc[0]['file_name']

    file_path_position = os.path.join(position_base_path, file_name_position)

    cut_h1 = match_row.iloc[0]['cutH1']
    offset_h2 = match_row.iloc[0]['offset_h2']
    first_vh2 = match_row.iloc[0]['firstVH2']
    
    return video_path, annotation_path, output_path, file_path_position, cut_h1, offset_h2, first_vh2
 
def reformatJson(path_timeline, path_output_jsonl, first_timestamp_ms, offset, offset_h2, first_vh2, fps):
    """
    Reformats a JSON timeline of events into a JSONL file with specific event details.
    Args:
        path_timeline (str): Path to the input JSON file containing the timeline of events.
        path_output_jsonl (str): Path to the output JSONL file where reformatted events will be written.
        first_timestamp_ms (int): The first timestamp in milliseconds.
        offset (int): Offset value for time synchronization.
        offset_h2 (int): Offset value for the second half of the game.
        first_vh2 (int): First value for the second half.
        fps (int): Frames per second for time synchronization.
    Returns:
        None
    """

    with open(path_timeline, 'r') as file:
        data = json.load(file)

    events = data.get('timeline', [])

    with open(path_output_jsonl, 'w') as file:
        for event in events:
            competitor = event.get('competitor', None)
            type = event.get('type')
            id = event.get('id')
            match_clock = event.get('match_clock', None)
            ball_possession = {
                'home': 'A',
                'away': 'B',
                'None': 'none'
            }.get(competitor, '')

            match type:
                case 'score_change':
                    pass_handball = ''
                    shot = 'successful'
                    unintentional_ball_release = ''
                    ball_reception = ''    
                    static_ball_action ='kick-off'
                    referee_decision = 'goal'
                case 'yellow_card':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''    
                    static_ball_action = ''
                    referee_decision = 'yellow'
                case 'red_card':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''    
                    static_ball_action = ''
                    referee_decision = 'red'
                case 'suspension':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''    
                    static_ball_action = ''
                    referee_decision = 'two min'
                case 'seven_m_awarded':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = 'penalty'
                    ball_reception = ''
                    static_ball_action = 'penalty'
                    referee_decision = '7m'
                case 'seven_m_missed':
                    pass_handball = ''
                    shot = 'saved'
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = 'penalty'
                    referee_decision = ''
                case 'break_start':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'period_score':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'period_start':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = 'kick-off'
                    referee_decision = ''
                    period_name = event.get('period_name', None)
                case 'shot_off_target':
                    pass_handball = ''
                    shot = 'off target'
                    unintentional_ball_release = 'other'
                    ball_reception = ''
                    static_ball_action = 'throw-in'
                    referee_decision = 'out of field'
                case 'shot_blocked': 
                    pass_handball = ''
                    shot = 'blocked/intercepted'
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'shot_saved':
                    pass_handball = ''
                    shot = 'saved'
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'steal':
                    pass_handball = 'intercepted'
                    shot = ''
                    unintentional_ball_release = 'successful interference'
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'suspension_over':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'technical_rule_fault':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = 'other'
                    ball_reception = ''
                    static_ball_action = 'free-throw'
                    referee_decision = 'other'
                case 'technical_ball_fault':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = 'other'
                    ball_reception = ''
                    static_ball_action = 'free-throw'
                    referee_decision = 'other'
                case 'substitution':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'timeout':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case 'timeout_over':
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
                case _:
                    pass_handball = ''
                    shot = ''
                    unintentional_ball_release = ''
                    ball_reception = ''
                    static_ball_action = ''
                    referee_decision = ''
            second_half = False       
            if match_clock is not None:
                match_minutes, match_seconds = map(int, match_clock.split(':'))
                threshold_minutes = 30
                threshold_seconds = 0
                if (match_minutes > threshold_minutes) or (match_minutes == threshold_minutes and match_seconds > threshold_seconds):
                    second_half = True                 
            if (type == 'period_start' and period_name == '2nd Half'):
                second_half = True
                
            reformatted_event = {
                't_start': int(synchronize_time(str(event.get('time', None)),second_half, first_timestamp_ms, offset, offset_h2, first_vh2, fps)),
                't_end': '-1',
                'annotator': "id: " + str(id),
                'labels': {
                    "type": type,
                    "pass": pass_handball,
                    "shot": shot,
                    "unintentional ball release": unintentional_ball_release,
                    "ball reception": ball_reception,
                    "static ball action": static_ball_action,
                    "referee decision": referee_decision,
                    "ball possession":ball_possession
                }
            }
            file.write(json.dumps(reformatted_event) + '\n')

# Main script
fps = 29.97  # Frames pro Sekunde
match_id = 23400275
video_path, path_timeline, path_output_jsonl, file_path_position, cut_h1, offset_h2, first_vh2 = get_paths_by_match_id(match_id)

first_timestamp_ms = load_first_timestamp_and_offset(file_path_position)
reformatJson(path_timeline, path_output_jsonl, first_timestamp_ms, cut_h1, offset_h2, first_vh2, fps) 