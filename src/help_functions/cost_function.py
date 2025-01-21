"""
This script demonstrates various functionalities of the `os` module
for interacting with the operating system.
"""
import os
import re
import unicodedata
from typing import Any

import floodlight.core.xy
import floodlight.io.kinexon as fliok
import numpy as np
import pandas as pd

import variables.data_variables as dv


def sync_event_data(events: dict[Any, Any], sequences: tuple[int, int, int],
                    match_id: int) -> dict[Any, Any]:
    """
    Synchronizes event data with position data for a given match.
    Args:
        events (dict): A dictionary containing event data.
        sequences (list): A list of sequences to be used for synchronization.
        match_id (int): The identifier for the match.
    Returns:
        dict: The updated events dictionary with synchronized position data.
    """

    filepath_data = get_pos_filepath(match_id)
    pos_data = fliok.read_position_data_csv(filepath_data)
    pid_dict, _, _, _ = fliok.get_meta_data(
        filepath_data)
    print(pid_dict)
    xids = fliok.create_links_from_meta_data(pid_dict, identifier="name")
    ball_num = find_key_position(pid_dict, "Ball")

    # events = add_information_to_events(events, match_id)
    for event in events.values():
        if event[8] is not None:
            pos_num = find_key_position(pid_dict, event[10])
            for i in xids.items():
                if i == event[10]:
                    event[22] = find_sequence(
                        sync_pos_data(xids[i], event[22],
                                      pos_data[pos_num], pos_data[ball_num],
                                      event[8]), sequences)
    return events


# def add_information_to_events(events: array, match_id: int) -> array:
#     (path_timeline, _, _, _, _, _, _, _) = help_functions
# reformatjson_methods.get_paths_by_match_id(
#         match_id)
#     # data: dict[Any, Any]
#     # with open(path_timeline, encoding="r") as file:
#     #     data = json.load(file)
#     for event in events:
#         event_type = event[0]
#         event_time = event[2]
#         # for (key, value) in data.items():
#         #     if event_type in value:
#         #         if event_time in value[event_type]:
#         #             event.append(value[event_type][event_time])
#         #             break


def get_pos_filepath(match_id: int,
                     season: dv.Season = dv.Season.SEASON_2020_2021,
                     basepath: str = r"D:\Handball") -> str:
    """
    Retrieves the file path for the positional data of a given match.
    Args:
        match_id (int): The ID of the match for which the positional data
        file path is required.
        season (dv.Season, optional): The season of the match. Defaults to
        dv.Season.SEASON_2020_2021.
        basepath (str, optional): The base directory path where the data is
        stored.
    Returns:
        str: The file path to the positional data of the specified match.
    """
    mapping_file = os.path.join(
        basepath, "HBL_Synchronization", f"mapping{season.value}.csv")
    # with open(mapping_file, mode='r', newline='') as file:
    #     reader = csv.DictReader(file)
    #     for row in reader:
    #         if int(row['match_id']) == match_id:
    #             pos_filepath = row['raw_pos_knx']
    #             break
    df = pd.read_csv(mapping_file, delimiter=";")
    match_row = df[df["match_id"] == int(match_id)]
    pos_filepath = match_row.iloc[0]["raw_pos_knx"]

    season_folder = season.value.replace("_", "-")
    return os.path.join(basepath, "HBL_Positions", season_folder,
                        pos_filepath)


def sync_pos_data(links: Any, t_event: int,
                  pos_data: floodlight.core.xy.XY,
                  ball_data: floodlight.core.xy.XY, pid: str,
                  threshold: float = 0.5) -> int:
    """
    Finds the last frame where the player had the ball before a specific
    event time.

    Args:
        pos_data: List of XY objects containing player and ball data.
        pid: The player ID (index of the XY object in pos_data).
        t_event: The frame index of the event.
        threshold: Distance threshold to determine if the player has the ball.

    Returns:
        The last frame index where the player had the ball before the event,
        or None if not found.
    """
    pid = normalize(pid)
    pid_num = get_pid_from_name(pid, links)
    # Get the XY object for the player
    player_data = pos_data.player(pid_num)  # Player's position data

    # Assuming the ball data is stored in the last XY object
    ball_data_1 = ball_data.player(0)
    ball_data_2 = ball_data.player(1)
    # Iterate backwards from the event time
    for t in range(t_event - 1, -1, -1):
        # Get player and ball positions for frame t
        player_position = player_data[t, :]  # X, Y of the player
        ball_position = ball_data_1[t, :]  # X, Y of the ball

        # Check for NaN values (indicates missing data)
        if np.isnan(player_position).any() or np.isnan(ball_position).any():
            continue  # Skip frames with missing data

        # Calculate the distance between player and ball
        distance = np.linalg.norm(player_position - ball_position)

        # Check if the distance is within the threshold
        if distance < threshold:
            return t  # Return the frame index

    for t in range(t_event - 1, -1, -1):
        # Get player and ball positions for frame t
        player_position = player_data[t, :]  # X, Y of the player
        ball_position = ball_data_2[t, :]  # X, Y of the ball

        # Check for NaN values (indicates missing data)
        if np.isnan(player_position).any() or np.isnan(ball_position).any():
            continue  # Skip frames with missing data

        # Calculate the distance between player and ball
        distance = np.linalg.norm(player_position - ball_position)

        # Check if the distance is within the threshold
        if distance < threshold:
            return t  # Return the frame index

    # If no possession is found before the event
    raise ValueError("No possession found before the event.")


def find_key_position(data: dict[Any, Any], key: str) -> int:
    """
    Find the position of a key in a dictionary.
    Args:
        data (dict): The dictionary to search in.
        key (str): The key to search for.
    Returns:
        int: The position (index) of the matched key in the dictionary.
    Raises:
        ValueError: If the key is not found in the dictionary.
    """

    keys_list = list(data.keys())
    for i, k in enumerate(keys_list):
        if key in k:
            return i  # Return the position of the matched key
    raise ValueError("Key not found")  # Key not found


def get_pid_from_name(pid: str, links: dict[str, str]) -> str:
    """
    Retrieves the normalized PID from a given name.
    Args:
        pid (str): The PID to be normalized and searched for.
        links (list): A list of tuples where each tuple contains a
        name and its corresponding number.
    Returns:
        str: The normalized PID if found, otherwise None.
    """

    links_normalized = {
        normalize(name): number for name, number in links.items()}

    if pid in links_normalized:
        return links_normalized[pid]
    raise ValueError("No pid for this name.")


def normalize(name: str) -> str:
    """
    Normalize a given name string by performing the following
    operations:
    1. Convert the name to ASCII by removing diacritics.
    2. If the name is in the format "Last, First", reorder it
    to "First Last".
    3. Remove special characters, such as underscores and
    other non-alphanumeric symbols.
    Args:
        name (str): The name string to be normalized.
    Returns:
        str: The normalized name string.
    """

    # Convert to ASCII by removing diacritics
    name = unicodedata.normalize('NFD', name).encode(
        'ascii', 'ignore').decode('utf-8')

    # Split and reorder "Last, First" -> "First Last"
    if ',' in name:
        last, first = [part.strip() for part in name.split(',', 1)]
        name = f"{first} {last}"

    # Remove special characters like underscores and other
    # non-alphanumeric symbols
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)

    return name.strip()


def find_sequence(time: int, sequences: tuple[Any, Any, Any]) -> Any:
    """
    Finds the sequence index for a given time.
    Args:
        time (int): The time to find the sequence for.
        sequences (tuple): A tuple of sequences, where each
        sequence is a tuple of
                           (start_time, end_time, sequence_index).
    Returns:
        int: The index of the sequence that the given time falls
        into, adjusted by -1.
             Returns None if no sequence is found for the given time.
    """

    for sequence in sequences:
        if sequence[0] <= time <= sequence[1]:
            return sequence[2]-1
    raise ValueError("No sequence found for this time.")


def calculate_group_id(match_id: int,
                       season: dv.Season = dv.Season.SEASON_2020_2021,
                       basepath: str = r"D:\Handball") -> Any:
    """
    Calculate and return distinct group IDs and group names for a
    given match.
    Args:
        match_id (int): The ID of the match.
        season (dv.Season, optional): The season of the match. Defaults
        to dv.Season.SEASON_2020_2021.
        basepath (str, optional): The base path where the data files
        are stored.
    Returns:
        list: A list of distinct group IDs and group names.
    """
    filepath = get_pos_filepath(match_id, season, basepath)
    df = pd.read_csv(filepath)
    distinct_pairs = df[['group id', 'group name']].drop_duplicates()
    print(distinct_pairs)
    return distinct_pairs
