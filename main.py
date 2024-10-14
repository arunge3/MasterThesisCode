import json
from datetime import datetime

# File paths
path_timeline = "D:\\Handball\\HBL_Events\\season_20_21\\EventTimeline\\sport_events_23400263_timeline.json"
path_output_jsonl = "D:\\Handball\\HBL_Events\\season_20_21\\EventJson\\sport_events_23400263_timeline_reformatted.jsonl"

# Frames per second of the video
fps = 29.97  # frames per second

# Starttime of the video
video_start_time = datetime.fromisoformat("2020-10-01T17:00:11+00:00")

# Method for converting event time to timeframe
def convert_event_time_to_timeframe(event_time_str):
    event_time = datetime.fromisoformat(event_time_str)
    time_diff_seconds = (event_time - video_start_time).total_seconds()
    timeframe = round(time_diff_seconds * fps) +56479
    return str(timeframe)

# Load json data from file
with open(path_timeline, 'r') as file:
    data = json.load(file)

# extract events from data
events = data.get('timeline', [])

# Create Jsonl File and write reformatted events
with open(path_output_jsonl, 'w') as file:
    for event in events:
        reformatted_event = {
            't_start': convert_event_time_to_timeframe(event.get('time', None)),
            't_end': '-1',
            'annotator': event.get('type'),
            'labels': {
                "formation": "A", 
                "pass": "D",
                # 'event_id': event.get('id'),
                # 'event_type': event.get('type'),
                # 'event_time': event.get('time'),
                # 'match_time': event.get('match_time', None),
                'competitor': event.get('competitor', None),
                # 'player_id': event.get('player', {}).get('id') if event.get('player') else None,
                # 'player_name': event.get('player', {}).get('name') if event.get('player') else None
            }
        }
        file.write(json.dumps(reformatted_event) + '\n')
