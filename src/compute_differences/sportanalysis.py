# TODO 1: Berrechne eine Accuary für die Events, die in einem
# Konterangriff stattfinden, die in einem Positionsangriff
# stattfinden etc.
# TODO 2: Evaluiere wie viele Personen sich in auf dem Feld
# befinden in der bestimmten Spielphase. Um dass dann mit
# einfließen zu lassen in die Accuracy Berechnung.
# TODO 3: Nur die Events in die Evaluation einbeziehen,
# für die ein neuer Wert gefunden wurde.
import re
import unicodedata
from typing import Any

import floodlight.io.kinexon as fliok
import numpy as np
import pandas as pd

from help_functions.pos_data_approach import get_pos_filepath


def evaluate_phase_events(events: pd.DataFrame,
                          sequences: list[tuple[int, int, int]]
                          ) -> pd.DataFrame:
    """
    Evaluates the accuracy of phase events in a handball match.
    """
    if 'phase' not in events.columns:
        events['phase'] = None
    for idx, event in enumerate(events.values):
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            (_, _, sequence) = get_sequence(event[24], sequences)
            if sequence is not None:
                events.iloc[idx, 28] = sequence
    return events


def get_sequence(timestamp: int, sequence: pd.DataFrame) -> pd.DataFrame:
    for i in range(len(sequence)):
        start_frame, end_frame, _ = sequence[i]
        if start_frame <= timestamp <= end_frame:
            return sequence[i]
    return (timestamp, timestamp, 0)


# def evaluate_counter_events(excel_path: str) -> None:
#     """
#     Evaluates the accuracy of counter events in a handball match.

#     Args:

#     excel_path (str): The path to the Excel file
#                       containing the event data.

#     Returns:
#         None
#     """
#     # Read the Excel file
#     df = pd.read_excel(excel_path)
#     specific_events = [
#         "score_change", "shot_saved", "shot_off_target",
#         "shot_blocked", "technical_rule_fault",
#         "seven_m_awarded", "steal", "technical_ball_fault"
#     ]
#     counter_events = []
#     pos_events = []
#     inactive_events = []
#     for event in df.values:
#         if event[0] in specific_events:
#             if event[28] in {3, 4}:
#                 counter_events.append(event)
#             elif event[28] in {1, 2}:
#                 pos_events.append(event)
#             elif event[28] == 0:
#                 inactive_events.append(event)

#     # Calculate accuracy for each approach
#     approaches = [
#         ("None", "none_correct"),
#         ("Baseline", "bl_correct"),
#         ("Rule-based", "rb_correct"),
#         ("Position-based", "pos_correct"),
#         ("Position Correction", "pos_cor_correct"),
#         ("Position Rule-based", "pos_rb_correct"),
#         ("Cost-based", "cost_correct"),
#         ("Cost-based Correction", "cost_cor_correct"),
#         ("Cost-based Rule-based", "cost_rb_correct")
#     ]

#     # Print results for counter attacks
#     print("\n=== COUNTER ATTACK EVENTS ACCURACY ===")
#     if counter_events:
#         for approach_name, correct_col in approaches:
#             # Find the index of the correct column in the dataframe
#             correct_col_idx = df.columns.get_loc(correct_col)
#             # Calculate accuracy if there are valid values
#             valid_values = [e[correct_col_idx]
#                             for e in counter_events
#                             if pd.notna(e[correct_col_idx])]
#             if valid_values:
#                 accuracy = sum(valid_values) / len(valid_values) * 100
#                 print(
#                     f"{approach_name} Accuracy: {accuracy:.2f}% "
#                     f"({sum(valid_values)}/{len(valid_values)})")
#             else:
#                 print(f"{approach_name} Accuracy: N/A (No valid data)")
#     else:
#         print("No counter attack events found.")

#     # Print results for positional attacks
#     print("\n=== POSITIONAL ATTACK EVENTS ACCURACY ===")
#     if pos_events:
#         for approach_name, correct_col in approaches:
#             correct_col_idx = df.columns.get_loc(correct_col)
#             valid_values = [e[correct_col_idx]
#                             for e in pos_events
#                             if pd.notna(e[correct_col_idx])]
#             if valid_values:
#                 accuracy = sum(valid_values) / len(valid_values) * 100
#                 print(
#                     f"{approach_name} Accuracy: {accuracy:.2f}% "
#                     f"({sum(valid_values)}/{len(valid_values)})")
#             else:
#                 print(f"{approach_name} Accuracy: N/A (No valid data)")
#     else:
#         print("No positional attack events found.")

#     # Print results for inactive phase
#     print("\n=== INACTIVE PHASE EVENTS ACCURACY ===")
#     if inactive_events:
#         for approach_name, correct_col in approaches:
#             correct_col_idx = df.columns.get_loc(correct_col)
#             valid_values = [e[correct_col_idx]
#                             for e in inactive_events
#                             if pd.notna(e[correct_col_idx])]
#             if valid_values:
#                 accuracy = sum(valid_values) / len(valid_values) * 100
#                 print(
#                     f"{approach_name} Accuracy: {accuracy:.2f}% "
#                     f"({sum(valid_values)}/{len(valid_values)})")
#             else:
#                 print(f"{approach_name} Accuracy: N/A (No valid data)")
#     else:
#         print("No inactive phase events found.")

#     # Print overall results
#     print("\n=== OVERALL EVENTS ACCURACY ===")
#     for approach_name, correct_col in approaches:
#         correct_col_idx = df.columns.get_loc(correct_col)
#         valid_values = [e[correct_col_idx]
#                         for e in df.values if pd.notna(e[correct_col_idx])]
#         if valid_values:
#             accuracy = sum(valid_values) / len(valid_values) * 100
#             print(
#                 f"{approach_name} Accuracy: {accuracy:.2f}% "
#                 f"({sum(valid_values)}/{len(valid_values)})")
#         else:
#             print(f"{approach_name} Accuracy: N/A (No valid data)")


def evaluation_of_players_on_field(match_id: int, events: pd.DataFrame,
                                   sequences: list[tuple[int, int, int]],
                                   ) -> pd.DataFrame:
    """
    Evaluates the number of players on the field at a given
    time in a handball match.

    This function iterates through events, identifies which sequence
    each event belongs to,
    and counts how many players from each team are on the field at
    that time by analyzing
    position data.

    Args:
        events (str): Path to the events file or event data.
        sequence (pd.DataFrame): DataFrame containing sequence
        information with timestamps.
        position_data (pd.DataFrame): DataFrame containing position
        data of players.

    Returns:
        None
    """
    filepath_data = get_pos_filepath(match_id)
    pos_data = fliok.read_position_data_csv(filepath_data)
    pid_dict, _, _, _ = fliok.get_meta_data(
        filepath_data)

    xids = fliok.create_links_from_meta_data(pid_dict, identifier="name")
    team_order = calculate_team_order(events)

    # Normalize team names in team_order
    normalized_team_order = []
    for team_name in team_order:
        # Remove accents and special characters
        normalized_name = unicodedata.normalize(
            'NFKD', team_name).encode('ASCII', 'ignore').decode('utf-8')
        # Remove any non-alphanumeric characters except spaces
        normalized_name = re.sub(r'[^\w\s]', '', normalized_name)
        # Convert to lowercase and strip whitespace
        normalized_name = normalized_name.lower().strip()
        normalized_team_order.append(normalized_name)

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
    team_home_name = normalized_team_order[0]
    team_away_name = normalized_team_order[1]
    for index, (name, id_value) in enumerate(normalized_xids.items()):
        # Check if team name is contained in the name or vice versa
        # to handle partial matches
        if team_home_name in name or name in team_home_name:
            team_home_position = pos_data[index]
        if team_away_name in name or name in team_away_name:
            team_away_position = pos_data[index]
    team_home_count = 0.0
    team_away_count = 0.0
    if 'home_team_count' not in events.columns:
        events['home_team_count'] = None
    if 'away_team_count' not in events.columns:
        events['away_team_count'] = None
    # events = add_information_to_events(events, match_id)
    for idx, event in enumerate(events.values):
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            sequence = get_sequence(event[24], sequences)
            if sequence is not None:
                team_home_count = get_players_count(
                    sequence, team_home_position)
                team_away_count = get_players_count(
                    sequence, team_away_position)
                events.iloc[idx, 26] = team_home_count
                events.iloc[idx, 27] = team_away_count
    return events


def get_players_count(sequence: pd.DataFrame,
                      position_data: pd.DataFrame) -> float:
    """
    Counts the number of players on the field during a specific sequence.
    Only counts players who are within the field boundaries:
    x: [-20, 20], y: [-10, 10]

    Args:
        sequence (pd.DataFrame): A row from the sequence
        DataFrame containing start_frame and end_frame.
        position_data (pd.DataFrame): DataFrame containing
        position data of players.

    Returns:
        float: The average number of players detected on the
        field during the sequence.
    """
    start_frame, end_frame, phase = sequence
    players_count = 0.0
    player_count_frame = 0
    player_count_frame_array = []

    for frame in range(start_frame, end_frame-1):
        for index in range((position_data.N+1)):
            player_pos = position_data.player(index)
            frame_data = player_pos[frame]

            if frame_data.any() and np.isfinite(frame_data).any():
                # Check if player is within field boundaries
                x, y = frame_data[0], frame_data[1]
                if -20 <= x <= 20 and -10 <= y <= 10:
                    player_count_frame += 1

        player_count_frame_array.append(player_count_frame)
        if player_count_frame > 7:
            print(f"Player count frame {frame} is {player_count_frame}")
        player_count_frame = 0

    # Calculate the mean number of players
    if player_count_frame_array:
        players_count = sum(player_count_frame_array) / \
            len(player_count_frame_array)
    else:
        players_count = 0

    if players_count > 7:
        print(f"Average player count is {players_count}")
    return players_count


def calculate_team_order(events: Any) -> list[str]:
    """
    Berechnet die Reihenfolge der Teams basierend auf den Ereignissen.

    Args:
        events: Die Event-Daten
    Returns:
        Liste der Teams in der Reihenfolge der Ereignisse
    """
    team_order = []
    for event in events.values:
        if event[10] is not None:
            if event[10] not in team_order:
                team_order.append(event[10])
    # Sort team order alphabetically
    team_order.sort()
    return team_order
