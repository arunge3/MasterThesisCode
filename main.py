import json

path_timeline = "D:\Handball\HBL_Events\season_20_21\EventTimeline\sport_events_23400263_timeline.json"
path_output = "D:\Handball\HBL_Events\season_20_21\EventJson\sport_events_23400263_timeline_reformatted.jsonl"
# path_video = "D:\Handball\HBL_Videos\season_2021\2020-10-01_754520_tsv_hannover-burgdorf-gwd_minden-720p-3000kbps.mp4"

# Load the JSON data from the file
with open(path_timeline, 'r') as file:
    data = json.load(file)

# Step 2: Extract events
events = data.get('timeline', {})

# Step 3: Reformat events
reformatted_events = []
for event in events:
    reformatted_event = {
        't_start': event.get('match_clock', None),
        't_end': event.get('match_clock', None),
        'annotator': '',
        'labels': {
            'event_id': event.get('id'),
            'event_type': event.get('type'),
            'event_time': event.get('time'),
            'match_time': event.get('match_time', None),
            'competitor': event.get('competitor', None),
            'player_id': event.get('player', {}).get('id') if event.get('player') else None,
            'player_name': event.get('player', {}).get('name') if event.get('player') else None
            },
        }       
    reformatted_events.append(reformatted_event)

# Step 4: Save the reformatted events to a new JSON file
with open(path_output, 'w') as file:
    json.dump(reformatted_events, file, indent=4)