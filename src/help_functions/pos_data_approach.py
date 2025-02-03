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
from rapidfuzz import process

import variables.data_variables as dv


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
    print(pid_dict)
    xids = fliok.create_links_from_meta_data(pid_dict, identifier="name")
    ball_num = find_key_position(pid_dict, "Ball")

    # events = add_information_to_events(events, match_id)
    for idx, event in enumerate(events.values):
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            if event[8] is not None:
                pos_num = find_key_position(pid_dict, event[10])
                for i in xids.items():
                    if i[0] == event[10]:
                        events.iloc[idx, 22] = (sync_pos_data(
                            i[1], event[22],
                            pos_data[pos_num],
                            pos_data[ball_num],
                            event[8]))
            elif event[14] is not None:
                pos_num = find_key_position(pid_dict, event[10])
                for i in xids.items():
                    if i[0] == event[10]:
                        events.iloc[idx, 22] = (sync_pos_data(
                            i[1], event[22],
                            pos_data[pos_num],
                            pos_data[ball_num],
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
                  ball_data: floodlight.core.xy.XY, pid: str,
                  threshold: float = 1) -> int:
    """
    Findet den letzten Frame vor einem bestimmten Ereignis, in dem ein
    Spieler den Ball hatte.

    Args:
        links: Dictionary mit Spieler-IDs und deren Zuordnungen
        t_event: Der Frame-Index des Ereignisses
        pos_data: XY-Objekt mit den Positionsdaten der Spieler
        ball_data: XY-Objekt mit den Positionsdaten des Balls
        pid: Die Spieler-ID (Name)
        threshold: Schwellenwert für die Distanz zum Ball (in Metern)

    Returns:
        int: Frame-Index des letzten Ballbesitzes vor dem Ereignis
    """
    # Normalisiere Spieler-ID und hole numerische ID
    pid = normalize(pid)
    pid_num = get_pid_from_name(pid, links)

    # Hole Positionsdaten des Spielers
    player_data = pos_data.player(pid_num)

    # Kombiniere die beiden Ball-Datensätze
    ball_data_1 = ball_data.player(0)
    ball_data_2 = ball_data.player(1)
    ball_positions = np.where(np.isnan(ball_data_1), ball_data_2,
                              ball_data_1)

    # Suche rückwärts vom Ereignis-Zeitpunkt
    for t in range(t_event - 1, max(-1, t_event - 300), -1):
        player_pos = player_data[t, :]
        ball_pos = ball_positions[t, :]

        # Überspringe Frames mit fehlenden Daten
        if np.isnan(player_pos).any() or np.isnan(ball_pos).any():
            continue

        # Berechne Distanz zwischen Spieler und Ball
        distance = np.linalg.norm(player_pos - ball_pos)

        if distance < threshold:
            return t

    # Wenn kein Ballbesitz gefunden wurde, gebe den ursprünglichen
    # Event-Frame zurück
    print(f"Kein Ballbesitz vor Frame {t_event} gefunden für {pid}")
    return t_event


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

    keys_list = list(data.keys())
    for i, k in enumerate(keys_list):
        k = unicodedata.normalize('NFD', k).encode(
            'ascii', 'ignore').decode('utf-8')
        if key in k:
            return i  # Return the position of the matched key
    raise ValueError("Key not found")  # Key not found


def get_pid_from_name(pid: str, links: dict[str, str]) -> int:
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
                             threshold: int = 80) -> int:
    """
    Finds the best match for a given PID in a dictionary of
    normalized PIDs.
    Args:

        pid (str): The PID to search for.
        links_normalized (dict): A dictionary of normalized PIDs.
        threshold (int, optional): The threshold for the fuzzy match.
        Defaults to 80.
    Returns:
        int: The best match for the PID if found, otherwise None.
    """
    # Use `extractOne` to find the best match for the pid
    best_match = process.extractOne(
        pid, links_normalized.keys(), score_cutoff=threshold)
    matched_key: int
    if best_match:
        _, _, matched_key = best_match
        return matched_key

    raise ValueError(f"No suitable match found for pid '{pid}'.")


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
    print(distinct_pairs)
    return distinct_pairs
