import csv
import json
import os
from collections import defaultdict
from typing import Any

import pandas as pd


def generate_paths(number: int, name: str,
                   base_path: str = r"D:\Handball\HBL_Events",
                   season: str = "season_20_21",
                   ) -> tuple[str, str, str, str, str, str, str,
                              str, str, str, str, str, str, str, str]:
    """
    Generate file paths dynamically based on inputs.

    :param base_path: Base directory for all paths
    :param season: Season folder name (e.g., "season_20_21")
    :param name: Name identifier for the game/event
    :param number: Unique number for the game/event
    :return: Dictionary of generated paths
    """
    base_path_season = os.path.join(base_path, season)
    datengrundlage = os.path.join(base_path_season, "Datengrundlagen")

    excel_path = os.path.join(
        datengrundlage, r"initial_excel", f"{name}.csv.xlsx")
    # Save the updated DataFrame
    name_new_game_path = os.path.join(datengrundlage, r"progressed_excel",
                                      f"{name}_updated.csv.xlsx")
    event_path = os.path.join(
        base_path_season,
        f"EventTimeline\\sport_events_{number}_timeline.json")
    csv_bl_path = os.path.join(
        datengrundlage, r"baseline", f"{number}_bl.csv")
    csv_rb_path = os.path.join(
        datengrundlage, r"rulebased", f"{number}_rb.csv")

    csv_none_path = os.path.join(
        datengrundlage, r"none", f"{number}_none.csv")
    csv_pos_path = os.path.join(datengrundlage, r"pos", f"{number}_pos_fl.csv")

    csv_pos_rb_path = os.path.join(
        datengrundlage, r"pos_rb", f"{number}_pos_rb_fl.csv")
    csv_pos_cor_path = os.path.join(
        datengrundlage, r"pos_cor", f"{number}_pos_cor_fl.csv")
    csv_cost_path = os.path.join(
        datengrundlage, r"cost_based", f"{number}_cost_based_fl.csv")
    csv_cost_cor_path = os.path.join(
        datengrundlage, r"cost_based_cor", f"{number}_cost_based_cor_fl.csv")
    csv_cost_rb_path = os.path.join(
        datengrundlage, r"cost_based_rb", f"{number}_cost_based_rb_fl.csv")
    output_path = os.path.join(
        datengrundlage, r"results", f"detailed_results_{number}.csv")
    # Directory containing the CSV files

    directory_results = os.path.join(datengrundlage, r"results")
    # Save results to CSV
    output_file_all = os.path.join(datengrundlage,
                                   r"results_summary.csv")

    return (excel_path, name_new_game_path, event_path, csv_bl_path,
            csv_rb_path, csv_none_path, csv_pos_path, csv_pos_rb_path,
            csv_pos_cor_path, csv_cost_path, csv_cost_cor_path,
            csv_cost_rb_path, output_path, directory_results, output_file_all)


# TODO Ich muss noch überprüfen, ob nicht nur die
# richtige Phasenbezeichnung
# zugeordnet wurde, sondern, ob auch die richtige Phase von der Zeit her
# zugeordnet wurde.
# TODO Ich muss noch schauen, ob die Regeln alle richtig sind
# TODO Manuell überprüfen, ob accuraxy stimmt


def calculate_if_correct(phase_true: int, phase_predicted: int,
                         time_start: int, time_end: int,
                         time_predicted: int) -> int:
    """
    Determines if the predicted phase and time are correct.
    Args:
        phase_true (int): The true phase value.
        phase_predicted (int): The predicted phase value.
        time_start (int): The start time of the valid time range.
        time_end (int): The end time of the valid time range.
        time_predicted (int): The predicted time value.
    Returns:
        int: Returns 1 if the predicted phase matches the true
        phase and the predicted time is within the valid time
        range, otherwise returns 0.
                        """
    if ((phase_true == phase_predicted)
            and (time_start <= time_predicted <= time_end)):
        return 1
    else:

        return 0


# # Read the files
# base_path = r"D:\Handball\HBL_Events\season_20_21"
# datengrundlage = r"Datengrundlagen"
# base_path_grundlage = os.path.join(base_path, datengrundlage)
# name_game_path = r"HSG Wetzlar_SG Flensburg-Handewitt_
# 04.10.2020_20-21.csv.xlsx"
# datei_pfad = os.path.join(base_path_grundlage, name_game_path)
# event_name = r"EventTimeline\sport_events_23400277_timeline.json"
# event_path = os.path.join(base_path, event_name)
# csv_pfad_name_bl = r"23400277_bl.csv"
# csv_pfad_bl = os.path.join(base_path_grundlage, csv_pfad_name_bl)
# csv_pfad_name_rb = r"23400277_rb.csv"
# csv_pfad_rb = os.path.join(base_path_grundlage, csv_pfad_name_rb)
# csv_pfad_none = os.path.join(base_path_grundlage, "23400277_none.csv")
# output_path = os.path.join(
#     base_path_grundlage, "detailed_results_23400277.csv")


# Rhein-Neckar Löwen_TVB Stuttgart_04.10.2020_20-21.csv.xlsx 23400275
# TSV GWD Minden_TSV Hannover-Burgdorf_01.10.2020_20-21.csv.xlsx 23400263
# HSG Wetzlar_THW Kiel_10.10.2020_20-21.csv.xlsx 23400307
# HSG Wetzlar_SG Flensburg-Handewitt_04.10.2020_20-21.csv.xlsx 23400277
# HSC 2000 Coburg_TBV Lemgo Lippe_01.10.2020_20-21.csv.xlsx 23400267

(excel_path, name_new_game_path, event_path, csv_bl_path,
 csv_rb_path, csv_none_path, csv_pos_path, csv_pos_rb_path,
 csv_pos_cor_path, csv_cost_path, csv_cost_cor_path,
 csv_cost_rb_path, output_path, directory_results, output_file_all) = (
     generate_paths(
         23400263,
         "TSV GWD Minden_TSV Hannover-Burgdorf_01.10.2020_20-21"))


df = pd.read_excel(excel_path)
with open(event_path, "r") as file:
    events_inital = json.load(file)

events_inital = events_inital["timeline"]
# Adjust the data types
df["eID"] = df["eID"].astype(str)
df["minute"] = df["minute"].fillna(0).astype(
    int)
df["second"] = df["second"].fillna(0).astype(
    int)
df = df.dropna(subset=["clips"])
# Add new columns to the DataFrame
if "Event_id" not in df.columns:
    df["Event_id"] = None

if "Phase_true" not in df.columns:
    df["Phase_true"] = None

if "Phase_start_true" not in df.columns:
    df["Phase_start_true"] = None

if "Phase_end_true" not in df.columns:
    df["Phase_end_true"] = None

if "Phase_None" not in df.columns:
    df["Phase_None"] = None

if "Phase_none_time" not in df.columns:
    df["Phase_none_time"] = None

if "none_correct" not in df.columns:
    df["none_correct"] = None

if "Phase_baseline" not in df.columns:
    df["Phase_baseline"] = None

if "Phase_bl_time" not in df.columns:
    df["Phase_bl_time"] = None

if "bl_correct" not in df.columns:
    df["bl_correct"] = None

if "Phase_rulebased" not in df.columns:
    df["Phase_rulebased"] = None

if "Phase_rb_time" not in df.columns:
    df["Phase_rb_time"] = None

if "rb_correct" not in df.columns:
    df["rb_correct"] = None

if "Phase_pos-based" not in df.columns:
    df["Phase_pos-based"] = None

if "Phase_pos_time" not in df.columns:
    df["Phase_pos_time"] = None

if "pos_correct" not in df.columns:
    df["pos_correct"] = None

if "Phase_pos_rb-based" not in df.columns:
    df["Phase_pos_rb-based"] = None

if "Phase_pos_rb_time" not in df.columns:
    df["Phase_pos_rb_time"] = None

if "pos_rb_correct" not in df.columns:
    df["pos_rb_correct"] = None

if "Phase_pos_cor-based" not in df.columns:
    df["Phase_pos_cor-based"] = None

if "Phase_pos_cor_time" not in df.columns:
    df["Phase_pos_cor_time"] = None

if "pos_cor_correct" not in df.columns:
    df["pos_cor_correct"] = None

if "Phase_cost-based" not in df.columns:
    df["Phase_cost-based"] = None

if "cost_time" not in df.columns:
    df["cost_time"] = None

if "cost_correct" not in df.columns:
    df["cost_correct"] = None

if "Phase_cost_based_rb-based" not in df.columns:
    df["Phase_cost_based_rb-based"] = None

if "cost_rb_time" not in df.columns:
    df["cost_rb_time"] = None

if "cost_rb_correct" not in df.columns:
    df["cost_rb_correct"] = None


# Exrahe Phase from the clips column
df["Phase_start_true"] = df["clips"].str.split("_").str[0]
# Exrahe Phase from the clips column
df["Phase_end_true"] = df["clips"].str.split("_").str[1]
# Exrahe Phase from the clips column
df["Phase_true"] = df["clips"].str.split("_").str[2]

# Convert the Phase to numeric
df["Phase_true"] = pd.to_numeric(df["Phase_true"], errors="coerce")

# Read the CSV files
df_csv_bl = pd.read_csv(csv_bl_path)
df_csv_rb = pd.read_csv(csv_rb_path)
df_csv_none = pd.read_csv(csv_none_path)
df_csv_pos = pd.read_csv(csv_pos_path)
df_csv_pos_rb = pd.read_csv(csv_pos_rb_path)
df_csv_pos_cor = pd.read_csv(csv_pos_cor_path)
df_csv_cost = pd.read_csv(csv_cost_path)
df_csv_cost_cor = pd.read_csv(csv_cost_cor_path)
df_csv_cost_rb = pd.read_csv(csv_cost_rb_path)
# mapping
for event in events_inital:
    event_id = event["id"]

    event_type = event["type"]
    if "match_clock" in event:
        match_clock = event["match_clock"]

        event_minutes, event_seconds = map(int, match_clock.split(":"))

        match_condition = (
            (df["eID"] == event_type) &
            (df["minute"] == (event_minutes)) &
            (df["second"] == (event_seconds))
        )
    else:
        match_condition = ((df["eID"] == event_type))

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id

df["Event_id"] = df["Event_id"].fillna(0).astype(
    int)
for index, row in df_csv_rb.iterrows():
    event_id = row['event_id']
    event_time = int(row['time'])
    phase = int(row['phase'])
    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_rulebased"] = phase
    df.loc[match_condition, "Phase_rb_time"] = event_time
    # Get the actual value of the phase and time from df (ground truth)
    if match_condition.any():
        phase_true = int(df.loc[match_condition, "Phase_true"].values[0])

        time_start = int(df.loc[match_condition, "Phase_start_true"].values[0])
        time_end = int(df.loc[match_condition, "Phase_end_true"].values[0])

        correct_phase = calculate_if_correct(
            phase_true, (phase), (time_start), (time_end), (event_time))

        df.loc[match_condition, "rb_correct"] = correct_phase


for index, row in df_csv_pos.iterrows():
    event_id = row['event_id']
    event_time = int(row['time'])
    phase = int(row['phase'])
    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_pos-based"] = phase
    df.loc[match_condition, "Phase_pos_time"] = event_time
    # Get the actual value of the phase and time from df (ground truth)
    if match_condition.any():
        phase_true = int(df.loc[match_condition, "Phase_true"].values[0])

        time_start = int(df.loc[match_condition, "Phase_start_true"].values[0])
        time_end = int(df.loc[match_condition, "Phase_end_true"].values[0])

        correct_phase = calculate_if_correct(
            phase_true, (phase), (time_start), (time_end), (event_time))

        df.loc[match_condition, "pos_correct"] = correct_phase
for index, row in df_csv_pos_rb.iterrows():
    event_id = row['event_id']
    event_time = int(row['time'])
    phase = int(row['phase'])
    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_pos_rb-based"] = phase
    df.loc[match_condition, "Phase_pos_rb_time"] = event_time
    # Get the actual value of the phase and time from df (ground truth)
    if match_condition.any():
        phase_true = int(df.loc[match_condition, "Phase_true"].values[0])

        time_start = int(df.loc[match_condition, "Phase_start_true"].values[0])
        time_end = int(df.loc[match_condition, "Phase_end_true"].values[0])

        correct_phase = calculate_if_correct(
            phase_true, (phase), (time_start), (time_end), (event_time))

        df.loc[match_condition, "pos_rb_correct"] = correct_phase

for index, row in df_csv_none.iterrows():
    event_id = row['event_id']
    event_time = int(row['time'])
    phase = int(row['phase'])

    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_None"] = phase
    df.loc[match_condition, "Phase_none_time"] = event_time
    # Get the actual value of the phase and time from df (ground truth)
    if match_condition.any():
        matched_rows = df.loc[match_condition, "Phase_true"]
        if len(matched_rows) == 1:

            phase_true = int(df.loc[match_condition, "Phase_true"].values[0])

            time_start = int(
                df.loc[match_condition, "Phase_start_true"].values[0])
            time_end = int(df.loc[match_condition, "Phase_end_true"].values[0])

            correct_phase = calculate_if_correct(
                phase_true, (phase), (time_start), (time_end), (event_time))

            df.loc[match_condition, "none_correct"] = correct_phase
        else:
            phase_true = int(df.loc[match_condition, "Phase_true"].values[1])

            time_start = int(
                df.loc[match_condition, "Phase_start_true"].values[1])
            time_end = int(df.loc[match_condition, "Phase_end_true"].values[1])

            correct_phase = calculate_if_correct(
                phase_true, (phase), (time_start), (time_end), (event_time))

            df.loc[match_condition, "none_correct"] = correct_phase


for index, row in df_csv_bl.iterrows():
    event_id = row['event_id']
    phase = row['phase']
    event_time = row['time']

    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_baseline"] = phase
    df.loc[match_condition, "Phase_bl_time"] = event_time

    # Check if there are any matching conditions
    if match_condition.any():
        # Get all matched rows for "Phase_true"
        matched_rows = df.loc[match_condition, "Phase_true"]

        # Ensure only one non-zero value exists
        if len(matched_rows) == 1:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[0]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "bl_correct"] = correct_phase
        else:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[1]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "bl_correct"] = correct_phase


for index, row in df_csv_pos_cor.iterrows():

    event_id = row['event_id']
    phase = row['phase']
    event_time = row['time']

    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_pos_cor-based"] = phase
    df.loc[match_condition, "Phase_pos_cor_time"] = event_time

    # Check if there are any matching conditions
    if match_condition.any():
        # Get all matched rows for "Phase_true"
        matched_rows = df.loc[match_condition, "Phase_true"]

        # Ensure only one non-zero value exists
        if len(matched_rows) == 1:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[0]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "pos_cor_correct"] = correct_phase
        else:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[1]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "pos_cor_correct"] = correct_phase
for index, row in df_csv_cost.iterrows():

    event_id = row['event_id']
    phase = row['phase']
    event_time = row['time']

    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_cost-based"] = phase
    df.loc[match_condition, "cost_time"] = event_time

    # Check if there are any matching conditions
    if match_condition.any():
        # Get all matched rows for "Phase_true"
        matched_rows = df.loc[match_condition, "Phase_true"]

        # Ensure only one non-zero value exists
        if len(matched_rows) == 1:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[0]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "cost_correct"] = correct_phase
        else:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[1]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "cost_correct"] = correct_phase
for index, row in df_csv_cost_cor.iterrows():

    event_id = row['event_id']
    phase = row['phase']
    event_time = row['time']

    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_cost_cor-based"] = phase
    df.loc[match_condition, "cost_cor_time"] = event_time

    # Check if there are any matching conditions
    if match_condition.any():
        # Get all matched rows for "Phase_true"
        matched_rows = df.loc[match_condition, "Phase_true"]

        # Ensure only one non-zero value exists
        if len(matched_rows) == 1:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[0]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "cost_cor_correct"] = correct_phase
        else:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[1]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "cost_cor_correct"] = correct_phase
for index, row in df_csv_cost_rb.iterrows():

    event_id = row['event_id']
    phase = row['phase']
    event_time = row['time']

    match_condition = (
        (df["Event_id"] == event_id)
    )

    # Write the event_id to the DataFrame
    df.loc[match_condition, "Event_id"] = event_id
    df.loc[match_condition, "Phase_cost_based_rb-based"] = phase
    df.loc[match_condition, "cost_rb_time"] = event_time

    # Check if there are any matching conditions
    if match_condition.any():
        # Get all matched rows for "Phase_true"
        matched_rows = df.loc[match_condition, "Phase_true"]

        # Ensure only one non-zero value exists
        if len(matched_rows) == 1:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[0]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "cost_rb_correct"] = correct_phase
        else:
            # Get the index of the single non-zero entry
            phase_true_index = matched_rows.index[1]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, "cost_rb_correct"] = correct_phase
df.to_excel(name_new_game_path, index=False)
print("Excel-Datei wurde aktualisiert und gespeichert.")


# # Accuracy for Phase_baseline
# baseline_correct = (df['Phase_true'] == df['Phase_baseline']).sum()
# baseline_total = len(df)
# baseline_accuracy = baseline_correct / baseline_total

# Accuracy for Phase_baseline
baseline_correct = (df['bl_correct'] == 1).sum()
baseline_total = len(df)
baseline_accuracy = baseline_correct / baseline_total

# Accuracy for Phase_baseline
none_correct = (df['none_correct'] == 1).sum()
none_accuracy = none_correct / baseline_total

# Accuracy for Phase_rulebased
rulebased_correct = (df['rb_correct'] == 1).sum()
rulebased_accuracy = rulebased_correct / baseline_total

# Accuracy for Phase_rulebased
pos_correct = (df['pos_correct'] == 1).sum()
pos_accuracy = pos_correct / baseline_total

# Accuracy for Phase_rulebased
pos_rb_correct = (df['pos_rb_correct'] == 1).sum()
pos_rb_accuracy = pos_rb_correct / baseline_total

# Accuracy for Phase_pos_cor-based
pos_cor_correct = (df['pos_cor_correct'] == 1).sum()
pos_cor_accuracy = pos_cor_correct / baseline_total

# Accuracy for Phase_cost-based
cost_correct = (df['cost_correct'] == 1).sum()
cost_accuracy = cost_correct / baseline_total

# Accuracy for Phase_cost-based
cost_rb_correct = (df['cost_rb_correct'] == 1).sum()
cost_rb_accuracy = cost_rb_correct / baseline_total

# Accuracy for Phase_cost-based
cost_cor_correct = (df['cost_cor_correct'] == 1).sum()
cost_cor_accuracy = cost_cor_correct / baseline_total


def calculate_accuracy_for_event_type(df: Any, event_type_column: Any,
                                      correct_column: Any) -> Any:

    # Find the accuracy for each event type
    accuracy_per_event = df.groupby(event_type_column).apply(
        lambda group: (group[correct_column] ==
                       1).sum() / len(group)
    )
    return accuracy_per_event


# Calculate the accuracy for each event type
baseline_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'bl_correct')
none_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'none_correct')
rulebased_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'rb_correct')
pos_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'pos_correct')
pos_rb_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'pos_rb_correct')
pos_cor_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'pos_cor_correct')
cost_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'cost_correct')
cost_rb_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'cost_rb_correct')
cost_cor_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'cost_cor_correct')


# Save to a CSV file
with open(output_path, 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header
    writer.writerow(["Approach", "Event Type", "Accuracy"])
    # Write overall accuracies
    writer.writerow(["None", "all", f"{none_accuracy:.4f}"])
    writer.writerow(["Baseline", "all", f"{baseline_accuracy:.4f}"])
    writer.writerow(["Rulebased", "all", f"{rulebased_accuracy:.4f}"])
    writer.writerow(["pos", "all", f"{pos_accuracy:.4f}"])
    writer.writerow(["pos_RB", "all", f"{pos_rb_accuracy:.4f}"])
    writer.writerow(["pos_COR", "all", f"{pos_cor_accuracy:.4f}"])
    writer.writerow(["Cost", "all", f"{cost_accuracy:.4f}"])
    writer.writerow(["Cost_RB", "all", f"{cost_rb_accuracy:.4f}"])
    writer.writerow(["Cost_COR", "all", f"{cost_cor_accuracy:.4f}"])

    # Write Phase_None accuracies
    for event, accuracy in none_accuracy_per_event.items():
        writer.writerow(["None", event, f"{accuracy:.4f}"])
    # Write Phase_Baseline accuracies
    for event, accuracy in baseline_accuracy_per_event.items():
        writer.writerow(["Baseline", event, f"{accuracy:.4f}"])
    # Write Phase_Rulebased accuracies
    for event, accuracy in rulebased_accuracy_per_event.items():
        writer.writerow(["Rulebased", event, f"{accuracy:.4f}"])
    for event, accuracy in pos_accuracy_per_event.items():
        writer.writerow(["pos", event, f"{accuracy:.4f}"])
    for event, accuracy in pos_rb_accuracy_per_event.items():
        writer.writerow(["pos_RB", event, f"{accuracy:.4f}"])
    for event, accuracy in pos_cor_accuracy_per_event.items():
        writer.writerow(["pos_COR", event, f"{accuracy:.4f}"])
    for event, accuracy in cost_accuracy_per_event.items():
        writer.writerow(["Cost", event, f"{accuracy:.4f}"])
    for event, accuracy in cost_rb_accuracy_per_event.items():
        writer.writerow(["Cost_RB", event, f"{accuracy:.4f}"])
    for event, accuracy in cost_cor_accuracy_per_event.items():
        writer.writerow(["Cost_COR", event, f"{accuracy:.4f}"])


print("Results saved to results.csv")


def calculate_all_accuracies(directory: str, output_file: str) -> None:
    """
    Calculate the average overall and event-type accuracies for
    each approach across all CSV files.

    :param directory: Path to the directory containing CSV files.
    :return: Two dictionaries: overall accuracies and event-type accuracies.
    """
    # Nested dict: {Approach: {Event Type: [accuracies]}}
    type_accuracies: dict[Any, Any] = defaultdict(lambda: defaultdict(list))
    # Iterate through all CSV files in the directory
    for file_name in os.listdir(directory):
        if file_name.endswith(".csv"):
            file_path = os.path.join(directory, file_name)
            try:
                # Read the CSV file
                df = pd.read_csv(file_path)

                # Extract event-type accuracies
                if 'Event Type' in df.columns and 'Accuracy' in df.columns:
                    for _, row in df.iterrows():
                        approach = row['Approach']
                        event_type = row['Event Type']
                        accuracy = row['Accuracy']
                        type_accuracies[approach][event_type].append(accuracy)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    # Calculate the average event-type accuracy for each approach
    avg_type_accuracies = {
        approach: {
            event_type: sum(acc_list) / len(acc_list) if acc_list else 0
            for event_type, acc_list in event_types.items()
        }
        for approach, event_types in type_accuracies.items()
    }
    # Prepare data for CSV
    rows: list[Any] = []

    # Add event-type accuracies
    rows.append([])  # Empty row for spacing
    rows.append(["Event-Type Accuracies"])
    rows.append(["Approach", "Event Type", "Average Accuracy"])
    for approach, event_types in avg_type_accuracies.items():
        for event_type, accuracy in event_types.items():
            rows.append([approach, event_type, f"{accuracy:.4f}"])

    # Write data to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)

    print(f"Results saved to {output_file}")
    print(type(rows))


# Calculate accuracies
calculate_all_accuracies(directory_results, output_file_all)
