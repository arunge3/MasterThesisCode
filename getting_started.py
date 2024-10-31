from floodlight.io.kinexon import read_position_data_csv, get_meta_data, create_links_from_meta_data
from floodlight.io.sportradar import read_event_data_json
import floodlight as fl
from floodlight import Code
from floodlight.core import pitch
import numpy as np
import pandas as pd
import template_matching
import rolling_mode
from floodlight.models.kinematics import DistanceModel
from floodlight.models.kinematics import VelocityModel

base_path = ""  # path to the data
season = ""  # season of the match
match = ""  # name of the match
path_positions = "D:\\Handball\\HBL_Positions\\21-22\\Bergischer HC_Frisch Auf! Göppingen_30.09.2021_21-22.csv"
path_events = "D:\\Handball\\HBL_Events\\season_21_22\\EventTimelines\\sport_events_28449852_timeline.json"
path_slice = "D:\\Handball\\HBL_Slicing\\season_21_22\\Bergischer HC_Frisch Auf! Göppingen_30.09.2021_21-22.csv.npy"

positions_path = f"{base_path}HBL_Positions\\{season}\\{match}"
phase_predictions_path = f"{base_path}HBL_Slicing\\{season}\\{match}.npy"
lookup_path = f"{base_path}\\HBL_Events\\lookup\\lookup_matches{season[6:]}.csv"

pitch = pitch.Pitch(xlim=(-20, 20), ylim=(-10, 10), unit="m", boundaries="fixed", sport="handball")

positions = read_position_data_csv(positions_path)
predictions = np.load(phase_predictions_path)
predictions = rolling_mode(predictions, 101)

slices = Code(predictions, "match_phases", {0: "inac", 1: "CATT-A", 2: "CATT-B", 3: "PATT-A", 4: "PATT-B"}, framerate=20)
lookup = pd.read_csv(lookup_path)
id_spr = lookup.loc[lookup["file_name"] == match, "match_id"].item()[15:]

match_id_sr = lookup.loc[lookup["file_name"] == match, "match_id"].item().split(":")[-1]
events_sr = pd.read_json(f"Y:\\Manuel\\Data\\Handball\\HBL_Events\\{season}\\EventSummaries\\sport_events_{match_id_sr}_summary.json")

home_team_statistics = events_sr["statistics"]["totals"]["competitors"][0]
away_team_statistics = events_sr["statistics"]["totals"]["competitors"][1]

meta_data, _, _, _ = get_meta_data(positions_path)
links = create_links_from_meta_data(meta_data, "league_id")

sequences = slices.find_sequences(return_type="list")
sequences = [x for x in sequences if x[1] - x[0] > slices.framerate]

# remove ball data
xy_lengths = [x.xy.shape[1] for x in positions]
ball_index = np.argmin(xy_lengths)
ball = positions.pop(ball_index)
xy1, xy2 = positions
xy_ids = list(meta_data.keys())
ball_id = xy_ids.pop(ball_index)
team_a_name, team_b_name = xy_ids

# map team_a/b on home/away and extract player sr IDs
if team_a_name == lookup.loc[lookup["file_name"] == match, "home_team_name"].item():
    team_a_id = lookup.loc[lookup["file_name"] == match, "home_team_id"].item()
    team_b_id = lookup.loc[lookup["file_name"] == match, "away_team_id"].item()
elif team_a_name == lookup.loc[lookup["file_name"] == match, "away_team_name"].item():
    team_a_id = lookup.loc[lookup["file_name"] == match, "away_team_id"].item()
    team_b_id = lookup.loc[lookup["file_name"] == match, "home_team_id"].item()
else:
    raise ValueError("team names don't match")

if team_a_id == home_team_statistics["id"]:
    team_a_player_ids = [x["id"].split(":")[-1] for x in home_team_statistics["players"]]
    team_b_player_ids = [x["id"].split(":")[-1] for x in away_team_statistics["players"]]
    home_team = "a"
elif team_a_id == away_team_statistics["id"]:
    team_a_player_ids = [x["id"].split(":")[-1] for x in away_team_statistics["players"]]
    team_b_player_ids = [x["id"].split(":")[-1] for x in home_team_statistics["players"]]
    home_team = "b"
else:
    raise ValueError("team ids dont match")

# identify goalkeepers
team_a_roles = {}
for pID in team_a_player_ids:
    player_profile = pd.read_json(f"Y:\\Manuel\\Data\\Handball\\HBL_Events\\general\\PlayerProfiles\\players_{pID}_profile.json")
    player_role = player_profile["player"]["type"]
    team_a_roles.update({pID: player_role})

team_b_roles = {}
for pID in team_b_player_ids:
    player_profile = pd.read_json(f"Y:\\Manuel\\Data\\Handball\\HBL_Events\\general\\PlayerProfiles\\players_{pID}_profile.json")
    player_role = player_profile["player"]["type"]
    team_b_roles.update({pID: player_role})

role_df_a = pd.DataFrame(list(team_a_roles.items()), columns=["pID", "role"])
column_df_a = pd.DataFrame(list(links[team_a_name].items()), columns=["pID", "xID"])

role_df_b = pd.DataFrame(list(team_b_roles.items()), columns=["pID", "role"])
column_df_b = pd.DataFrame(list(links[team_b_name].items()), columns=["pID", "xID"])

teamsheet_a = pd.merge(role_df_a, column_df_a, on="pID")
teamsheet_b = pd.merge(role_df_b, column_df_b, on="pID")

gk_ids_a = teamsheet_a.loc[teamsheet_a["role"] == "G", 'xID']
gk_ids_b = teamsheet_b.loc[teamsheet_b["role"] == "G", 'xID']

# set goal keepers to nan
for xID in gk_ids_a:
    xy1.xy[:, 2*xID:2*xID + 2] = np.NaN
for xID in gk_ids_b:
    xy2.xy[:, 2*xID:2*xID + 2] = np.NaN

xy_objects = {"a": xy1, "b": xy2}

# calculate intensity
distances = {}
velocities = {}
for team in xy_objects:
    dm = DistanceModel()
    dm.fit(xy_objects[team])
    distances.update({team: dm.distance_covered()})

    vm = VelocityModel()
    vm.fit(xy_objects[team])
    velocities.update({team: vm.velocity()})

# template matching

phase_to_team_def= {3: "b", 4: "a"}

templates = pd.read_json("C:\\Users\\ke6564\\Desktop\\Studium\\Promotion\\Handball\\FormationDetection\\templates.json")


i = 2
phase = sequences[i]
formations = []
for i, phase in enumerate(sequences):
    start, end, phase_type = phase
    if phase_type in [3, 4]:
        coords_def = xy_objects[phase_to_team_def[phase_type]].slice(start, end)

        # detect playing direction
        phase_mean_x = np.nanmean(coords_def.x)

        if phase_mean_x > 0:
            playing_direction = "lr"
        elif phase_mean_x < 0:
            playing_direction = "rl"
        else:
            ValueError("Dafuq is the playing direction")

        # reflect if playing direction is lr, because of template orientation
        if playing_direction == "lr":
            coords_def.reflect(axis="y")
            coords_def.reflect(axis="x")
            playing_direction = "rl"

        # translate coords to match templates (origin = bottom left)
        # coords_def.translate((20, 10))

        fsims = template_matching(coords_def, templates)
        top_formation = sorted(fsims.items(), key=lambda x:x[1], reverse=True)[0][0]

        # identify next phase
        next_phase = 0
        j = i
        while next_phase == 0:
            j += 1
            if j < len(sequences):
                next_phase = sequences[j][2]
            else:
                break

        # phase intensity
        dist_def = np.nansum(distances[phase_to_team_def[phase_type]].slice(start, end).property)
        vel_def = np.nanmean(velocities[phase_to_team_def[phase_type]].slice(start, end).property)

        formation_dict = {
            "match": match, "start": start, "end": end,
            "phase_type": phase_type, "formation": top_formation, "next_phases": next_phase,
            "dist_def": dist_def, "vel_def": vel_def
        }

        formations.append(formation_dict)