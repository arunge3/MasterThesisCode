from datetime import datetime as dt
import numpy as np
import pytz
import helpFunctions.reformatJson_Methods as helpFuctions
from existing_code.rolling_mode import rolling_mode
from floodlight import Code

def adjustTimestamp(match_id): 
    """
    Adjusts the timestamps of events in a match to align with the positional data timeframe.
    Args:
        match_id (int): The unique identifier for the match.
    Returns:
        None
    This function performs the following steps:
    1. Retrieves various paths and parameters related to the match using the match_id.
    2. Loads the first timestamp of the positional data.
    3. Loads and reformats the event data to adjust timestamps based on the positional data.
    4. Converts the first positional data timestamp to a datetime object.
    5. Adjusts the timestamps of each event to align with the positional data timeframe.
    """
    # Paths
    _, path_timeline, _, positions_path, cut_h1, offset_h2, first_vh2, match= helpFuctions.get_paths_by_match_id(match_id)
    first_time_pos_str, first_time_pos_unix, fps_positional = helpFuctions.load_first_timestamp_position(positions_path)    
    
    # Framerate of the video
    fps_video = 29.97
    # Load event data and adjust timestamps
    event_json = helpFuctions.reformatJson_Time_only(path_timeline, first_time_pos_str, cut_h1, offset_h2, first_vh2, fps_video)
    
    competitors = event_json["sport_event"]["competitors"]
    # Extract team names and qualifiers
    team_info = {team["name"]: team["qualifier"] for team in competitors}
    events = event_json.get('timeline', [])

    # Match start timestamp 
    first_time_stamp_event = helpFuctions.getFirstTimeStampEvent(path_timeline)
    print("match_start_datetime:", first_time_stamp_event)
    
    # timezone
    utc_timezone = pytz.utc

    # timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix/1000 # Unix timestamp
    positional_data_start_date = dt.fromtimestamp(positional_data_start_timestamp).replace(tzinfo=utc_timezone)
    print("positional_data_start_date:", positional_data_start_date)

    # Change the time of the events to the timeframe of the positional data
    for event in events:
        t_start = event["time"]
        event_time_seconds = (t_start-cut_h1) / fps_video
        event_absolute_timestamp = positional_data_start_timestamp + event_time_seconds
        event_timestamp_date = dt.fromtimestamp(event_absolute_timestamp).replace(tzinfo=utc_timezone)
        print("event_timestamp_date:", event_timestamp_date)
        event_timeframe= (event_timestamp_date-positional_data_start_date).seconds*fps_positional
        event["time"] = event_timeframe
        
    return events, team_info

def calculate_sequences(match_id):
    """
    Calculate sequences of game phases for a given match.
    Args:
        match_id (str): The identifier for the match.
    Returns:
        list: A list of sequences where each sequence is represented as a tuple (start_frame, end_frame).
              Only sequences longer than one frame duration are included.
    """
    
    # Paths
    base_path = "D:\\Handball\\"
    season = "season_20_21"  
    _, _, _, positions_path, _, _, _, match= helpFuctions.get_paths_by_match_id(match_id)
    _, _, fps_positional = helpFuctions.load_first_timestamp_position(positions_path)
    phase_predictions_path = f"{base_path}HBL_Slicing\\{season}\\{match}.npy"
    
    # Load positional data and phase predictions
    predictions = np.load(phase_predictions_path)
    predictions = rolling_mode(predictions, 101)
    slices = Code(predictions, "match_phases", {0: "inac", 1: "CATT-A", 2: "CATT-B", 3: "PATT-A", 4: "PATT-B"}, fps_positional)

    # get Sequences of the game phases
    sequences = slices.find_sequences(return_type="list")
    sequences = [x for x in sequences if x[1] - x[0] > slices.framerate]
    
    return sequences

def synchronize_events(events, sequences, team_info):
    """
    Synchronize events with sequences and team information.
    This function processes a list of events and sequences, and synchronizes them based on the provided team information.
    It assigns teams based on alphabetical order, determines their locations (home or away), and maps events to the corresponding teams.
    Args:
        events (list of dict): A list of event dictionaries, where each dictionary contains event details such as type, time, and competitor.
        sequences (list): A list of sequences to be synchronized with the events.
        team_info (dict): A dictionary containing team names as keys and their locations (home or away) as values.
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
    location_to_team = {
        team_a_location: "A",
        team_b_location: "B"
    }
    # Define positions for each phase
    phase_positions = {
        0: 0,  # (inac)
        1: 1,  # (CATT-A)
        2: 2,  # (CATT-B)
        3: 3,  # (PATT-A)
        4: 4   # (PATT-B)
    }
    for event in events:
        competitor_location = event.get("competitor")
        if competitor_location in location_to_team:
            team_ab = location_to_team[competitor_location]  # Map "home"/"away" to "A" or "B"
            print(f"Event Type: {event['type']}, Competitor: Team {team_ab} ({competitor_location})")
        else:
            # Handle events without a competitor if necessary
            print(f"Event Type: {event['type']}, Competitor: None")
        type = event["type"]
        time = event["time"]
        if type == "score_change": 
            if (give_last_event != "seven_m_awarded"):
                calculate_correct_phase(time, sequences, team_ab, event)
        elif type == "seven_m_awarded" or type == "shot_off_target" or type == "shot_saved" or type == "shot_blocked" or type == "technical_ball_fault" or type == "technical_rule_fault" or type == "steal":
           calculate_correct_phase(time, sequences, team_ab, event)
        # if type in ["yellow_card", "red_card", "suspension_over", "technical_rule_fault", "technical_ball_fault", "steal", "shot_saved", "shot_off_target", "shot_blocked", "seven_m_awarded", "seven_m_missed", "yellow_card", "red_card"]:
    return events, sequences

def searchPhase(time, sequences, competitor):
    """
    Searches for the last matching phase before a given time for a specified competitor.
    Args:
        time (int): The time before which to search for the phase.
        sequences (list of tuples): A list of tuples where each tuple contains 
                                    (start_time, end_time, phase).
        competitor (str): The competitor for whom the phase is being searched. 
                          Should be either "A" or "B".
    Returns:
        int or None: The end time of the last matching phase before the given time 
                     for the specified competitor, or None if no valid phase is found.
    """
    
    # Go through sequences in reverse to find the last matching phase before `time`
    for _, end, phase in reversed(sequences):
        if end <= time:
            if (phase == 1 or phase == 3) and competitor == "A":
                return end-1  # Return the end of this phase for competitor "A"
            elif (phase == 2 or phase == 4) and competitor == "B":
                return end-1  # Return the end of this phase for competitor "B"
    return None  # Return None if no valid phase was found before `time`

def give_last_event(events, time):
    """
    Returns the last event from the list of events that occurred before or at the given time,
    excluding certain types of events.
    Args:
        events (list of dict): A list of event dictionaries, where each dictionary contains
                               information about an event, including a "time" key and a "type" key.
        time (int or float): The time threshold to compare events against.
    Returns:
        dict or None: The last event dictionary that occurred before or at the given time and is not
                      of type "suspension", "yellow_card", "red_card", or "suspension_over". If no
                      such event is found, returns None.
    """
    
    for event in reversed(events):
        if event["time"] <= time:
            if event["type"] not in ["suspension", "yellow_card", "red_card", "suspension_over"]:
                return event
    return None

def calculate_correct_phase(time, sequences, team_ab, event):
    """
    Determines the correct phase for a given event based on the provided time, sequences, and team.
    Args:
        time (float): The time of the event.
        sequences (list of tuples): A list of tuples where each tuple contains the start time, end time, and phase.
        team_ab (str): The team identifier, either "A" or "B".
        event (dict): The event dictionary which may be modified with a new time if the phase is incorrect.
    Returns:
        None: The function modifies the event dictionary in place if the phase is incorrect.
    """
    
    # TODO 7m missed in der Regel in einer inaktiven Phase 
    # TODO timeout genommen immer am ende einer Phase oder innerhalb einer inaktiven Phase
    # TODO timeout ende immer in inaktiver phase vermutlich gegen ende von inaktiver Phase 
    # TODO kann man anhand der Positionsdaten ermitteln, ob ein Ball im Tor war oder nicht? INlusive Zeitstempel?
    
    # Find the y value on the continuous line for this event's time (t_start)
        # Define positions for each phase
    phase_positions = {
        0: 0,  # (inac)
        1: 1,  # (CATT-A)
        2: 2,  # (CATT-B)
        3: 3,  # (PATT-A)
        4: 4   # (PATT-B)
    }
    phase = None
    for start, end, phase in sequences:
        if start <= time < end:
            phase = phase_positions[phase]
            break
    if (phase == 1 or phase == 3 and team_ab == "A") or (phase == 2 or phase == 4 and team_ab == "B"):
        print("correct Phase")
    else:
        new_time = searchPhase(time, sequences, team_ab)
        if new_time is not None:
            event["time"] = new_time

