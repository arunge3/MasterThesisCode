"""
This module implements template matching functionality for
handball match analysis. It provides functions for processing position
data, calculating team metrics, and identifying formations during
different phases of the game.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""
# from matplotlib import pyplot as plt
import json
from typing import Any, Union

# import floodlight.core.pitch
import floodlight.core.xy as xy
# import floodlight as fl
import matplotlib
import numpy as np
import pandas as pd
from floodlight import Code
from floodlight.io.kinexon import (create_links_from_meta_data, get_meta_data,
                                   read_position_data_csv)
from floodlight.models.kinematics import DistanceModel, VelocityModel

from existing_code import template_matching
from existing_code.rolling_mode import rolling_mode

# from floodlight.io.sportradar import read_event_data_json


# import help_functions.reformatjson_methods

matplotlib.use("TkAgg", force=True)

print("Switched to:", matplotlib.get_backend())


def get_path_template_matching(
    match_id: int, season: str = "season_20_21",
    base_path: str = "D:\\Handball\\",
    csv_file: str = (
        r"D:\Handball\HBL_Synchronization\mapping20_21.csv"),
    lookup_file: str = (
        r"D:\Handball\HBL_Events\lookup\lookup_matches_20_21.csv")
) -> tuple[Any, Any, Any, Any, Any, Any, Any]:
    """
    Get the path to the template matching files.
    Args:



        match_id: The id of the match.
        season: The season of the match.
        base_path: The base path to the data.
        csv_file: The csv file with the match ids.
        lookup_file: The lookup file with the match ids.
    Returns:
        positions_path: The path to the positions file.
        phase_predictions_path: The path to the phase predictions
        file.
        lookup_path: The path to the lookup file.
        template_path: The path to the template file.
        match: The match id.
        events_sr: The events data.
        player_profiles: The player profiles.
    """
    df = pd.read_csv(csv_file, delimiter=";")
    match_row = df[df["match_id"] == int(match_id)]

    if match_row.empty:
        return None, None, None, None, None, None, None
    match = match_row.iloc[0]["raw_pos_knx"]
    positions_path = f"{base_path}HBL_Positions\\20-21\\{match}"
    phase_predictions_path = f"{base_path}HBL_Slicing\\{season}\\{match}.npy"

    lookup_path = (f"{base_path}\\HBL_Events\\lookup\\"
                   f"lookup_matches{season[6:]}.csv")
    events_sr = pd.read_json(
        f"{base_path}\\HBL_Events\\{season}\\"
        f"EventSummaries\\sport_events_{match_id}_summary.json")

    lookup_df = pd.read_csv(lookup_file)
    lookup_row = lookup_df[lookup_df["match_id"]
                           == f"sr:sport_event:{match_id}"]

    if lookup_row.empty:
        return None, None, None, None, None, None, None

    player_profiles = f"{base_path}\\HBL_Events\\general\\PlayerProfiles"

    return (positions_path, phase_predictions_path, lookup_path,
            "D:\\processing_code\\templates.json", match, events_sr,
            player_profiles)


def load_and_prepare_data(
    positions_path: str,
    phase_predictions_path: str
) -> tuple[xy.XY, Code, list[tuple[int, int, int]]]:
    """
    Loads and prepares the positions and phase predictions data.
    Args:
        positions_path: The path to the positions data.
        phase_predictions_path: The path to the phase predictions data.
    Returns:
        positions: The positions data.
        slices: The slices data.
        sequences: The sequences data.
    """
    positions = read_position_data_csv(positions_path)
    predictions = np.load(phase_predictions_path)
    predictions = rolling_mode(predictions, 101)

    slices = Code(
        predictions,
        "match_phases",
        {0: "inac", 1: "CATT-A", 2: "CATT-B", 3: "PATT-A", 4: "PATT-B"},
        framerate=20,
    )
    sequences = slices.find_sequences(return_type="list")
    sequences = [x for x in sequences if x[1] - x[0] > slices.framerate]

    return positions, slices, sequences


def separate_ball_data(positions: list[xy.XY],
                       meta_data: dict[str, Any]
                       ) -> tuple[xy.XY, xy.XY, str, str, xy.XY]:
    """
    Separates the ball data from the player data.
    Args:

        positions: The positions data.
        meta_data: The meta data.
    Returns:
        xy1: The xy data of team A.
        xy2: The xy data of team B.
        team_a_name: The name of team A.
        team_b_name: The name of team B.
    """
    xy_lengths = [x.xy.shape[1] for x in positions]
    ball_index = np.argmin(xy_lengths)
    ball = positions.pop(ball_index)
    xy1, xy2 = positions
    xy_ids = list(meta_data.keys())

    xy_ids.pop(ball_index)
    # ball_id = xy_ids.pop(ball_index)
    team_a_name, team_b_name = xy_ids

    return xy1, xy2, team_a_name, team_b_name, ball


def calculate_team_metrics(xy_objects: dict[str, xy.XY]
                           ) -> tuple[dict[str, float],
                                      dict[str, float]]:
    """
    Calculates distance and velocity for both teams.
    Args:
        xy_objects: The xy objects.
    Returns:
        distances: The distances.
        velocities: The velocities.
    """
    distances = {}
    velocities = {}
    for team in xy_objects:

        dm = DistanceModel()
        dm.fit(xy_objects[team])
        distances.update({team: dm.distance_covered()})

        vm = VelocityModel()
        vm.fit(xy_objects[team])
        velocities.update({team: vm.velocity()})

    return distances, velocities


def process_formation_phase(phase: tuple[int, int, int],
                            xy_objects: dict[str, xy.XY],
                            phase_to_team_def: dict[int, str],
                            template_dict: dict[str, np.ndarray],
                            distances: dict[Any, Any],
                            velocities: dict[Any, Any],
                            match: str, sequences: list[tuple[int, int, int]],
                            phase_index: int
                            ) -> Any:
    """
    Processes a single formation phase.
    Args:
        phase: The phase to process.
        xy_objects: The xy objects.
        phase_to_team_def: The phase to team definition.
        template_dict: The template dictionary.
        distances: The distances.
        velocities: The velocities.
        match: The match.
        sequences: The sequences.
        phase_index: The phase index.
    Returns:
        The formation dictionary.
    """
    start, end, phase_type = phase
    if phase_type not in [3, 4]:

        return None

    coords_def = xy_objects[phase_to_team_def[phase_type]].slice(start, end)
    phase_mean_x = np.nanmean(coords_def.x)

    playing_direction = "lr" if phase_mean_x > 0 else "rl"

    if playing_direction == "lr":
        coords_def.reflect(axis="y")
        coords_def.reflect(axis="x")

    fsims = template_matching.template_matching(coords_def, template_dict)
    top_formation = sorted(
        fsims.items(), key=lambda x: x[1], reverse=True)[0][0]

    next_phase = get_next_phase(sequences, phase_index)

    dist_def = np.nansum(
        distances[phase_to_team_def[phase_type]].slice(start, end).property)
    vel_def = np.nanmean(
        velocities[phase_to_team_def[phase_type]].slice(start, end).property)

    return {
        "match": match,
        "start": start,
        "end": end,
        "phase_type": phase_type,
        "formation": top_formation,
        "next_phases": next_phase,
        "dist_def": dist_def,
        "vel_def": vel_def
    }


def get_next_phase(sequences: list[tuple[int, int, int]],
                   current_index: int
                   ) -> int:
    """
    Ermittelt die nächste Phase.
    """
    next_phase = 0
    j = current_index
    while next_phase == 0:

        j += 1
        if j < len(sequences):
            next_phase = sequences[j][2]
        else:
            break
    return next_phase


def run_template_matching(match_id: int
                          ) -> list[dict[str, Union[float, str, int]]]:
    """

    Runs the template matching for a match.
    Args:
        match_id: The match id.
    Returns:
        The formation dictionary.
    """
    paths = get_path_template_matching(match_id)
    if any(path is None for path in paths):

        return []

    (positions_path, phase_predictions_path, lookup_path,
     template_path, match, events_sr, player_profiles
     ) = paths

    # Daten laden und vorbereiten
    positions, _, sequences = load_and_prepare_data(
        positions_path, phase_predictions_path)

    # Metadaten laden
    meta_data, _, _, _ = get_meta_data(positions_path)
    links = create_links_from_meta_data(meta_data, "sensor_id")

    # Ball- und Spielerdaten trennen
    xy1, xy2, team_a_name, team_b_name, _ = separate_ball_data(
        positions, meta_data)

    # Team-Mapping und Spieler-IDs
    home_team_statistics = events_sr["statistics"]["totals"]["competitors"][0]
    away_team_statistics = events_sr["statistics"]["totals"]["competitors"][1]
    lookup = pd.read_csv(lookup_path)
    team_mapping = map_teams_and_extract_player_ids(
        team_a_name, match, lookup, home_team_statistics, away_team_statistics
    )
    team_a_player_ids, team_b_player_ids = team_mapping[2:4]

    # Torhüter identifizieren und filtern
    xy_objects = identify_and_filter_goalkeepers(
        team_a_player_ids, team_b_player_ids, player_profiles,
        links, team_a_name, team_b_name, xy1, xy2
    )

    # Team-Metriken berechnen
    distances, velocities = calculate_team_metrics(xy_objects)

    # Templates laden
    with open(template_path, "r", encoding="utf-8") as f:
        templates = json.load(f)
    template_dict = {k: np.array(v).reshape(-1, 2)
                     for k, v in templates.items()}

    # Phasen verarbeiten
    phase_to_team_def = {3: "b", 4: "a"}
    formations = []

    for i, phase in enumerate(sequences):
        formation_dict = process_formation_phase(
            phase, xy_objects, phase_to_team_def, template_dict,
            distances, velocities, match, sequences, i
        )
        if formation_dict:
            formations.append(formation_dict)
    # print(formations)
    return formations


def map_teams_and_extract_player_ids(team_a_name: str, match: str,
                                     lookup: pd.DataFrame,
                                     home_team_statistics: dict[str, Any],
                                     away_team_statistics: dict[str, Any]
                                     ) -> tuple[str, str, list[str],
                                                list[str], str]:
    """

    Assigns teams (A/B) to home/away teams and extracts player IDs.
    Args:
        team_a_name: Name of team A
        match: Match identifier
        lookup: DataFrame with team information
        home_team_statistics: Statistics of the home team
        away_team_statistics: Statistics of the away team


    Returns:
        team_a_id: ID of team A
        team_b_id: ID of team B
        team_a_player_ids: List of player IDs of team A
        team_b_player_ids: List of player IDs of team B
        home_team: String "a" or "b" to identify the home team

    """
    # map team_a/b on home/away and extract player sr IDs
    if (team_a_name == lookup.loc[lookup["file_name"] == f"{match}",
                                  "home_team_name"].item()):
        team_a_id = lookup.loc[lookup["file_name"]
                               == f"{match}", "home_team_id"].item()
        team_b_id = lookup.loc[lookup["file_name"]
                               == f"{match}", "away_team_id"].item()
    elif (team_a_name == lookup.loc[lookup["file_name"] == f"{match}",
                                    "away_team_name"].item()):
        team_a_id = lookup.loc[lookup["file_name"]
                               == f"{match}", "away_team_id"].item()
        team_b_id = lookup.loc[lookup["file_name"]
                               == f"{match}", "home_team_id"].item()
    else:
        raise ValueError("team names don't match")

    if team_a_id == home_team_statistics["id"]:
        team_a_player_ids = [x["id"].split(":")[-1]
                             for x in home_team_statistics["players"]]
        team_b_player_ids = [x["id"].split(":")[-1]
                             for x in away_team_statistics["players"]]
        home_team = "a"
    elif team_a_id == away_team_statistics["id"]:
        team_a_player_ids = [x["id"].split(":")[-1]
                             for x in away_team_statistics["players"]]
        team_b_player_ids = [x["id"].split(":")[-1]
                             for x in home_team_statistics["players"]]
        home_team = "b"
    else:
        raise ValueError("team ids dont match")

    return (team_a_id, team_b_id, team_a_player_ids,
            team_b_player_ids, home_team)


def identify_and_filter_goalkeepers(team_a_player_ids: list[str],
                                    team_b_player_ids: list[str],
                                    player_profiles: str,
                                    links: dict[str, dict[str, str]],
                                    team_a_name: str,
                                    team_b_name: str,
                                    xy1: xy.XY,
                                    xy2: xy.XY
                                    ) -> dict[str, xy.XY]:
    """
    Identifies goalkeepers of both teams and filters their
    positions from the movement data.


    Args:
        team_a_player_ids: List of player IDs of team A
        team_b_player_ids: List of player IDs of team B
        player_profiles: Path to the player profiles
        links: Dictionary with mappings between player IDs and sensor IDs
        team_a_name: Name of team A
        team_b_name: Name of team B
        xy1: Movement data of team A
        xy2: Movement data of team B


    Returns:
        dict: Dictionary with filtered movement data of both teams
    """
    team_a_roles = {}
    for pid in team_a_player_ids:

        try:
            with open(
                    f"{player_profiles}\\players_{pid}_profile.json", "r",
                    encoding="utf-8"
            ) as file:
                player_profile = json.load(file)

            if ("player" in player_profile
                    and "type" in player_profile["player"]):
                player_role = player_profile["player"]["type"]
            else:
                player_role = "Unknown"

                print(f"Warning: 'type' not found for player {pid}")

            team_a_roles[pid] = player_role

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading profile for player {pid}: {e}")
            team_a_roles[pid] = "Unknown"

    team_b_roles = {}
    for pid in team_b_player_ids:
        try:
            with open(
                f"{player_profiles}\\players_{pid}_profile.json", "r",
                encoding="utf-8"
            ) as file:
                player_profile = json.load(file)

            if ("player" in player_profile
                    and "type" in player_profile["player"]):
                player_role = player_profile["player"]["type"]
            else:
                player_role = "Unknown"

                print(f"Warning: 'type' not found for player {pid}")

            team_b_roles[pid] = player_role

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading profile for player {pid}: {e}")
            team_b_roles[pid] = "Unknown"

    role_df_a = pd.DataFrame(
        list(team_a_roles.items()), columns=["pID", "role"])
    column_df_a = pd.DataFrame(
        list(links[team_a_name].items()), columns=["pID", "xID"])

    role_df_b = pd.DataFrame(
        list(team_b_roles.items()), columns=["pID", "role"])
    column_df_b = pd.DataFrame(
        list(links[team_b_name].items()), columns=["pID", "xID"])

    teamsheet_a = pd.merge(role_df_a, column_df_a, on="pID")
    teamsheet_b = pd.merge(role_df_b, column_df_b, on="pID")

    gk_ids_a = teamsheet_a.loc[teamsheet_a["role"] == "G", "xID"]
    gk_ids_b = teamsheet_b.loc[teamsheet_b["role"] == "G", "xID"]

    # Filter goalkeepers
    for xid in gk_ids_a:
        xy1.xy[:, 2 * xid: 2 * xid + 2] = np.NaN
    for xid in gk_ids_b:
        xy2.xy[:, 2 * xid: 2 * xid + 2] = np.NaN

    return {"a": xy1, "b": xy2}


# run_template_matching(23400513)
