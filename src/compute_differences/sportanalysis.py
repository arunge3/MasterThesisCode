"""
This module provides functions for analyzing and computing various metrics
from handball match data. It includes functions for evaluating event accuracy,
calculating team order, and counting players on the field at specific times.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""
import re
import unicodedata
from typing import Any, Union

import floodlight.io.kinexon as fliok
import numpy as np
import pandas as pd

from help_functions.pos_data_approach import get_pos_filepath


def next_phase(events: pd.DataFrame,
               sequences: list[tuple[int, int, int]]
               ) -> pd.DataFrame:
    """
    Determines the next phase for each event based on the sequences.
    Args:
        events: The event data
        sequences: The sequences of events
    Returns:
        The event data with the next phase
    """
    if 'next_phase' not in events.columns:
        events['next_phase'] = None
    for idx, event in enumerate(events.values):
        if event[0] in ["score_change", "shot_saved", "shot_off_target",
                        "shot_blocked", "technical_rule_fault",
                        "seven_m_awarded", "steal", "technical_ball_fault"]:
            phase = get_next_phase(sequences, event[24])
            if phase is not None:
                events.iloc[idx, 29] = phase
    return events


def get_next_phase(sequences: list[tuple[int, int, int]], timestamp: int
                   ) -> Union[int, None]:
    """
    Determines the next phase for a given sequence.

    Args:
        sequences: List of sequences (start, end, phase)
        timestamp: The timestamp of the event

    Returns:
        int: The next phase
    """
    for i in range(len(sequences)):
        sequnce = sequences[i]
        if sequnce[0] <= timestamp <= sequnce[1]:

            return find_next_non_null_phase(sequences, i)
    return None


def find_next_non_null_phase(sequences: list[tuple[int, int, int]],
                             current_idx: int) -> Union[int, None]:
    """
    Finds the next non-null phase entry after the current index.

    Args:
        sequences: List of sequences (start, end, phase)
        current_idx: The current index from which to search

    Returns:
        tuple: (Index of the next non-null entry, phase value) or
        (None, None) if no entry is found
    """
    for idx in range(current_idx + 1, len(sequences)):
        sequence = sequences[idx]
        if sequence[2] is not None and sequence[2] != 0:
            return sequence[2]
    return None


def evaluate_phase_events(events: pd.DataFrame,
                          sequences: list[tuple[int, int, int]]
                          ) -> pd.DataFrame:
    """
    Evaluates the accuracy of phase events in a handball match.
    Args:
        events: The event data
        sequences: The sequences of events
    Returns:
        The event data with the phase
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
    """
    Gets the sequence for a given timestamp.
    Args:
        timestamp: The timestamp of the event
        sequence: The sequence of events
    Returns:
        The sequence of events
    """
    for i in range(len(sequence)):
        start_frame, end_frame, _ = sequence[i]
        if start_frame <= timestamp <= end_frame:
            return sequence[i]
    return (timestamp, timestamp, 0)


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
    team_home_position = None
    team_away_position = None
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
        sequence (pd.DataFrame): A row from the sequence DataFrame
        containing start_frame and end_frame.
        position_data (pd.DataFrame): DataFrame containing
        position data of players.

    Returns:
        float: The average number of players detected, when there
        are more than 40 frames (2 seconds) with less than 7
        players, it will be set to 7.0
    """
    start_frame, end_frame, _ = sequence
    players_count = 0.0
    player_count_frame = 0
    player_count_frame_array = []
    frames_less_than_7_players = 0

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
        if player_count_frame < 7:
            frames_less_than_7_players += 1

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
    if frames_less_than_7_players > 40:
        players_count = 7.0

    return players_count


def calculate_team_order(events: Any) -> list[str]:
    """
    Calculates the order of teams based on the events.

    Args:
        events: The event data
    Returns:
        List of teams in the order of events
    """
    team_order = []
    for event in events.values:
        if event[10] is not None:
            if event[10] not in team_order:
                team_order.append(event[10])
    # Sort team order alphabetically
    team_order.sort()
    return team_order
