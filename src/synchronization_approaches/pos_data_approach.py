"""
This script demonstrates various functionalities of the `os` module
for interacting with the operating system.
Author:
    @Annabelle Runge
Date:
    2025-04-29
"""
import os
import re
import unicodedata
from typing import Any

import floodlight.core.xy
import floodlight.io.kinexon as fliok
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from rapidfuzz import fuzz

import help_functions.position_helpers as position_helpers
import variables.data_variables as dv
from preprocessing.template_matching.template_start import \
    fuzzy_match_team_name


def sync_event_data_pos_data(events: Any,
                             match_id: int) -> Any:
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
    # print(pid_dict)
    xids = fliok.create_links_from_meta_data(pid_dict, identifier="name")
    ball_num = find_key_position(pid_dict, "Ball")
    ball_positions, _ = position_helpers.prepare_ball_data(pos_data[ball_num])
    # Normalize names in xids dictionary
    normalized_xids = {}
    for name, id_value in xids.items():
        # Remove accents and special characters
        normalized_name = unicodedata.normalize(
            'NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
        # Remove any non-alphanumeric characters except spaces
        normalized_name = re.sub(r'[^\w\s]', '', normalized_name)
        # Convert to lowercase and strip whitespace
        normalized_name = normalized_name.lower().strip()
        normalized_xids[normalized_name] = id_value

    # events = add_information_to_events(events, match_id)
    for idx, event in enumerate(events.values):
        last_event = give_last_event_fl(events.values, event[24])
        if last_event is not None:
            last_event = last_event[0]
        if (event[0] == "score_change" and last_event ==
                "seven_m_awarded"):
            events.iloc[idx, 0] = "seven_m_scored"
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            if event[8] is not None:
                pos_num = find_key_position(pid_dict, event[10])
                # Normalize the player name from the event for comparison
                event_player_name = event[10]
                if event_player_name:
                    # Apply the same normalization as above
                    normalized_event_player = (unicodedata.normalize(
                        'NFKD', event_player_name
                    ).encode('ASCII', 'ignore').decode('utf-8'))
                    normalized_event_player = re.sub(
                        r'[^\w\s]', '', normalized_event_player)
                    normalized_event_player = (normalized_event_player
                                               .lower().strip())
                for i in normalized_xids.items():
                    # Compare with both original and normalized names
                    if fuzzy_match_team_name(
                            normalized_event_player, i[0]):
                        events.iloc[idx, 24] = (sync_pos_data(
                            i[1], event[24],
                            pos_data[pos_num],
                            ball_positions,
                            event[8]))
            elif event[14] is not None:
                pos_num = find_key_position(pid_dict, event[10])
                # Normalize the player name from the event for comparison
                event_player_name = event[10]
                if event_player_name:
                    # Apply the same normalization as above
                    normalized_event_player = (unicodedata.normalize(
                        'NFKD', event_player_name
                    ).encode('ASCII', 'ignore').decode('utf-8'))
                    normalized_event_player = re.sub(
                        r'[^\w\s]', '', normalized_event_player)
                    normalized_event_player = (normalized_event_player
                                               .lower().strip())
                for i in normalized_xids.items():
                    if fuzzy_match_team_name(
                            normalized_event_player, i[0]):
                        events.iloc[idx, 24] = (sync_pos_data(
                            i[1], event[24],
                            pos_data[pos_num],
                            ball_positions,
                            event[14]["name"]))

    return events


# def add_information_to_events(events, match_id: int):
#     (path_timeline, _, _, _, _, _, _, _) = (
    # help_functions.reformatjson_methods.get_paths_by_match_id(
#         match_id))


#     data: dict[Any, Any]
#     with open(path_timeline, encoding="r") as file:
#         data = json.load(file)
#     for event in events:
#         event_type = event[0]
#         event_time = event[2]
#         # for (key, value) in data.items():
#         #     if event_type in value:
#         #         if event_time in value[event_type]:
#         #             event.append(value[event_type][event_time])
#         #             break

# def find_event_id(event_type, event_time, data):
#     for (key, value) in data.items():
#         if event_type in value:
#             if event_time in value[event_type]:
#                 return value[event_type][event_time]
#     return None
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
                  ball_positions: floodlight.core.xy.XY, pid: str,
                  threshold: float = 0.99) -> int:
    """
    This function finds the last frame before a specific event where a
    player had the ball.

    Args:
        links: Dictionary with player IDs and their assignments
        t_event: The frame index of the event
        pos_data: XY-object with the player positions
        ball_data: XY-object with the ball positions
        pid: The player ID (name)
        threshold: Threshold for the distance to the ball (in meters)

    Returns:
        int: Frame index of the last ball possession before the event
    """
    # Normalize player ID and get numerical ID
    pid = normalize(pid)
    pid_num = get_pid_from_name(pid, links)

    # Get player positions data
    player_data = pos_data.player(pid_num)

    pos_index = False
    ball_index = False
    none_idx = 0
    max_time = t_event-500
    # Search backwards from the event time
    for t in range(t_event - 1, max(-1, max_time), -1):
        try:
            player_pos = player_data[t, :]
            ball_pos = ball_positions[t, :]
        except Exception as e:
            print(f"Warning: Error accessing position data at frame {t}: {e}")
            continue

        # Skip frames with missing data
        if np.isnan(player_pos).any() or np.isnan(ball_pos).any():
            none_idx += 1
            continue

        # Calculate distance between player and ball
        distance = np.linalg.norm(player_pos - ball_pos)

        if distance < 0.3:
            return t
    # plot_test(max_time, t_event, player_data, ball_positions, pid)
    if none_idx >= 499:
        for t in range(max_time, 0, -1):
            if np.isnan(player_pos).any() or np.isnan(ball_pos).any():
                none_idx += 1
            else:
                break
    if none_idx > 10:
        print(f"Game was interrupted for {none_idx} frames")
        max_time = max_time-none_idx
    for t in range(t_event - 1, max(-1, max_time), -1):
        try:
            player_pos = player_data[t, :]
        except Exception as e:
            print(
                f"Warning: Error accessing player position data at frame {t}: "
                f"{e}")
            continue
        try:
            ball_pos = ball_positions[t, :]
        except Exception as e:
            print(
                f"Warning: Error accessing ball position data at frame {t}: "
                f"{e}")
            continue
        if not np.isnan(player_pos).any():
            pos_index = True
        if not np.isnan(ball_pos).any():
            ball_index = True
        # Skip frames with missing data
        if np.isnan(player_pos).any() or np.isnan(ball_pos).any():
            continue

        # Calculate distance between player and ball
        distance = np.linalg.norm(player_pos - ball_pos)

        if distance < threshold:
            return t
    else:

        print(
            f"No ball possession found before frame {t_event} for {pid}")
    # If no ball possession is found, return the original event frame
    if not pos_index:
        print(
            f"No player position data found for {pid} from frame {t_event} "
            f"to {max_time}")
    if not ball_index:
        print(f"No ball data found from frame {t_event} to {max_time}")
    # plot_test(max_time, t_event, player_data, ball_positions, pid)
    print(f"No ball possession found before frame {t_event} for {pid}")
    return t_event


def plot_test(max_time: int, t_event: int,
              player_data: Any, ball_positions: Any, pid: str) -> None:
    """
    Plots the movement path of a player and the ball.
    Args:
        max_time (int): The maximum time of the data.
        t_event (int): The time of the event.
        player_data (Any): The player data.
        ball_positions (Any): The ball positions.
        pid (str): The player ID.
    """
    # Define the time range for plotting
    plot_range = range(max_time, t_event)
    # Prepare data for plotting
    try:
        player_positions = player_data[plot_range]
        ball_positions = ball_positions[plot_range]

        # Create plot
        plt.figure(figsize=(16, 8))  # Aspect ratio 2:1 for 40x20m field

        # Plot player positions
        plt.plot(player_positions[:, 0],
                 player_positions[:, 1], 'b.-', label='Player')

        # Plot ball positions
        plt.plot(ball_positions[:, 0],
                 ball_positions[:, 1], 'r.-', label='Ball')

        plt.title(f'Movement path of player {pid} and ball')
        plt.xlabel('X-Position (m)')
        plt.ylabel('Y-Position (m)')
        plt.legend()
        plt.grid(True)

        # Set axis limits to exact Handball field dimensions
        plt.xlim(-20, 20)  # Length of the field (40m)
        plt.ylim(-10, 10)  # Width of the field (20m)
        plt.gca().set_aspect('equal')  # Force aspect ratio 2:1

        plt.show()
    except Exception as e:
        print(f"Error accessing player position data for plot: {e}")
        # player_positions = np.array([])  # Empty array as fallback


def find_key_position(data: dict[Any, Any], key: str) -> int:
    """
    Find the position of a key in a dictionary.
    Args:
        data (dict): The dictionary to search in.
        key (str): The key to search for.
    Returns:
        int: The position (index) of the matched key in the
        dictionary.
    Raises:
        ValueError: If the key is not found in the dictionary.
    """
    key = key.lower()
    keys_list = list(data.keys())
    for i, k in enumerate(keys_list):
        k = unicodedata.normalize('NFD', k).encode(
            'ascii', 'ignore').decode('utf-8').lower()
        if key in k:
            return i  # Return the position of the matched key
    raise ValueError("Key not found")  # Key not found


def get_pid_from_name(pid: str, links: dict[str, str]) -> Any:
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
    return get_pid_with_fuzzy_match(pid, links_normalized)


def get_pid_with_fuzzy_match(pid: str, links_normalized: dict[str, str],
                             threshold: int = 80) -> Any:
    """
    Finds the best match for a given PID in a dictionary of
    normalized PIDs.
    Args:
        pid (str): The PID to search for.
        links_normalized (dict): Dictionary with normalized PIDs.
        threshold (int, optional): Threshold for the fuzzy match.
        Default: 80

    Returns:
        int: The best match for the PID

    Raises:
        ValueError: If no matching PID is found
    """
    # Split the search name into first and last name
    search_first, search_last = split_name(pid)

    best_match = ""
    best_score = 0

    for key in links_normalized.keys():
        # Split the comparison name
        current_first, current_last = split_name(key)

        # Calculate the match for the last name (weight: 70%)
        lastname_score = fuzz.ratio(search_last, current_last) * 0.7

        # Calculate the match for the first name (weight: 30%)
        firstname_score = fuzz.ratio(search_first, current_first) * 0.3

        # Total score
        total_score = lastname_score + firstname_score

        if total_score > best_score:
            best_score = total_score
            best_match = key

    # Check the threshold (converted to 0-100 scale)
    if best_score * 100 >= threshold:
        return links_normalized[best_match]

    raise ValueError(
        f"No matching PID found for pid '{pid}'.")


def split_name(name: str) -> tuple[str, str]:
    """
    Splits a name into first and last name.
    Args:
        name (str): The name to split.
    Returns:
        tuple: A tuple containing the first and last name.
    """
    parts = name.split()
    return parts[0], " ".join(parts[1:]) if len(parts) > 1 else ""


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


# def find_sequence(time: int, sequences: tuple[Any, Any, Any]) -> Any:
#     """
#     Finds the sequence index for a given time.
#     Args:
#         time (int): The time to find the sequence for.
#         sequences (tuple): A tuple of sequences, where each
#         sequence is a tuple of
#                            (start_time, end_time, sequence_index).
#     Returns:
#         int: The index of the sequence that the given time falls
#         into, adjusted by -1.
#              Returns None if no sequence is found for the given time.
#     """

#     for sequence in sequences:
#         if sequence[0] <= time <= sequence[1]:
#             return sequence[1]-1
#     raise ValueError("No sequence found for this time.")


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
    # print(distinct_pairs)
    return distinct_pairs


def give_next_event_fl(events: pd.DataFrame, time: int) -> Any:
    """
    Returns the next event from the list of events that occurred after the
    given time, excluding certain types of events.
    """
    for event in (events):
        if event[24] > time:

            if event[0] not in [
                "suspension",
                "yellow_card",
                "red_card",
                "suspension_over",
            ]:
                return event
    return None


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
    for event in reversed(events):
        if event[24] < time:

            if event[0] not in [
                "suspension",
                "yellow_card",
                "red_card",
                "suspension_over",
            ]:
                return event
    return None
