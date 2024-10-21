import json
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import pytz

def load_first_timestamp_and_offset(file_path):
    # Einlesen der CSV-Datei
    df = pd.read_csv(file_path)
    # Extrahieren des ersten Zeitstempels in ms
    first_timestamp_ms = df['ts in ms'].iloc[0]
    # Unix timestamp
    unix_timestamp = first_timestamp_ms / 1000  # Convert from milliseconds to seconds
    # Convert to human-readable date and time
    date_time = str(datetime.fromtimestamp(unix_timestamp,  tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
    
    return date_time


def synchronize_time(event_time_str, first_timestamp_str, offset_fr, fps):
    utc_timezone = pytz.utc
    
    event_time = datetime.fromisoformat(event_time_str).replace(tzinfo=utc_timezone)
    first_timestamp = datetime.fromisoformat(first_timestamp_str).replace(tzinfo=utc_timezone)
    
    
    delta = event_time - first_timestamp
    delta_fr= delta.seconds*fps

    # Berechnung der synchronisierten Zeit
    synced_time = delta_fr+ offset_fr
    return synced_time

def get_paths_by_match_id(match_id):
    
    csv_file = r"D:\Handball\HBL_Synchronization\mapping20_21.csv"
    video_base_path = r"D:\Handball\HBL_Videos\season_2021"
    annotation_base_path = r"D:\Handball\HBL_Events\season_20_21\EventTimeline"
    output_base_path = r"D:\Handball\HBL_Events\season_20_21\EventJson"
    position_base_path = r"D:\Handball\HBL_Positions\20-21"
    
    df = pd.read_csv(csv_file, delimiter=';')
    test  = df[df['match_id'] == int(match_id)]
    # Suche nach dem Eintrag für die gegebene match_id
    match_row =  df[df['match_id'] == int(match_id)]
    
    if match_row.empty:
        return None, None, None,  None, None, None 

    # Extrahiere die relevanten Informationen
    video_file = match_row.iloc[0]['raw_video']
    annotation_file = f"sport_events_{match_id}_timeline.json"
    output_file = f"sport_events_{match_id}_timeline_reformatted.jsonl"
    
    # Erstelle die vollständigen Pfade
    video_path = os.path.join(video_base_path, video_file)
    annotation_path = os.path.join(annotation_base_path, annotation_file)
    output_path = os.path.join(output_base_path, output_file)
    
     # Extract and construct the file path for positions
    home_team_name = match_row.iloc[0]['home_team_name'].replace(" ", "_")  # Replace spaces with underscores
    away_team_name = match_row.iloc[0]['away_team_name'].replace(" ", "_")  # Replace spaces with underscores
    match_date = match_row.iloc[0]['date'].replace(".", "-")  # Replace dots with dashes

    # Construct the position file path
    file_path_position = os.path.join(position_base_path, f"{home_team_name}_{away_team_name}_{match_date}_20-21.csv")
    cut_h1 = match_row.iloc[0]['cutH1']
    offset_h2 = match_row.iloc[0]['offset_h2']
    first_vh2 = match_row.iloc[0]['firstVH2']
    
    return video_path, annotation_path, output_path, file_path_position, cut_h1, offset_h2, first_vh2

def reformatJson(path_timeline, path_output_jsonl  , first_timestamp_ms, offset, fps):    
    """ Reformats a JSON timeline of events into a JSONL file with specific event details.

    Args:
        path_timeline (str): Path to the input JSON file containing the timeline of events.
        path_output_jsonl (str): Path to the output JSONL file where reformatted events will be written.
        fps (int): Frames per second of the video, used to convert event times.
        video_start_time (str): Start time of the video, used for time calculations.
    """
    # Load json data from file
    with open(path_timeline, 'r') as file:
        data = json.load(file)

    # extract events from data
    events = data.get('timeline', [])

    # Create Jsonl File and write reformatted events
    with open(path_output_jsonl, 'w') as file:
        for event in events:
            competitor = event.get('competitor', None)
            type = event.get('type')
            id = event.get('id')
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
            
            reformatted_event = {
                't_start': int(synchronize_time(str(event.get('time', None)), first_timestamp_ms, offset, fps)),
                't_end': '-1',
                'annotator': id,
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




# Beispielparameter
# file_path_Position = r"D:\Handball\HBL_Positions\20-21\Die Eulen Ludwigshafen_SC DHFK Leipzig_01.10.2020_20-21.csv"
# file_mapping = r"D:\Handball\HBL_Synchronization\mapping20_21.csv"
# offset = -7730  # ms
# event_time_str = "2020-10-01T18:24:56+00:00"  # Beispiel-Event-Zeit
# Nutzung der Methoden


fps = 29.97  # Frames pro Sekunde
match_id = 23400265
video_path, path_timeline, path_output_jsonl, file_path_position, cut_h1, offset_h2, first_vh2 = get_paths_by_match_id(match_id)

first_timestamp_ms = load_first_timestamp_and_offset(file_path_position)
reformatJson(path_timeline, path_output_jsonl, first_timestamp_ms, cut_h1, fps) 