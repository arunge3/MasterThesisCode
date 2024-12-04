import json
import os
from typing import Any

import pandas as pd

# TODO Ich muss noch überprüfen, ob nicht nur die
# richtige Phasenbezeichnung
# zugeordnet wurde, sondern, ob auch die richtige Phase von der Zeit her
# zugeordnet wurde.
# TODO Ich muss noch schauen, ob die Regeln alle richtig sind
# TODO Manuell überprüfen, ob accuraxy stimmt


def calculate_if_correct(phase_true: int, phase_predicted: int,
                         time_start: int, time_end: int,
                         time_predicted: int) -> int:
    if ((phase_true == phase_predicted) and (time_start
                                             <= time_predicted <= time_end)):
        return 1
    else:
        return 0


# Read the files
base_path = r"D:\Handball\HBL_Events\season_20_21"
datengrundlage = r"Datengrundlagen"
base_path_grundlage = os.path.join(base_path, datengrundlage)
name_game_path = r"HSC 2000 Coburg_TBV Lemgo Lippe_01.10.2020_20-21.csv.xlsx"
datei_pfad = os.path.join(base_path_grundlage, name_game_path)
event_name = r"EventTimeline\sport_events_23400267_timeline.json"
event_path = os.path.join(base_path, event_name)
csv_pfad_name_bl = r"23400267_bl.csv"
csv_pfad_bl = os.path.join(base_path_grundlage, csv_pfad_name_bl)
csv_pfad_name_rb = r"23400267_rb.csv"
csv_pfad_rb = os.path.join(base_path_grundlage, csv_pfad_name_rb)

df = pd.read_excel(datei_pfad)


with open(event_path, "r") as file:
    events_inital = json.load(file)

events_inital = events_inital["timeline"]
print(df.dtypes)
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

if "Phase_ml-based" not in df.columns:
    df["Phase_ml-based"] = None

if "ml_correct" not in df.columns:
    df["ml_correct"] = None

# Exrahe Phase from the clips column
df["Phase_start_true"] = df["clips"].str.split("_").str[0]
# Exrahe Phase from the clips column
df["Phase_end_true"] = df["clips"].str.split("_").str[1]
# Exrahe Phase from the clips column
df["Phase_true"] = df["clips"].str.split("_").str[2]

# Convert the Phase to numeric
df["Phase_true"] = pd.to_numeric(df["Phase_true"], errors="coerce")

# Read the CSV files
df_csv_bl = pd.read_csv(csv_pfad_bl)
df_csv_rb = pd.read_csv(csv_pfad_rb)
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
print(df["Event_id"])
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
        print(type(phase_true), type(phase), type(
            time_start), type(time_end), type(event_time))

        correct_phase = calculate_if_correct(
            phase_true, (phase), (time_start), (time_end), (event_time))

        df.loc[match_condition, "rb_correct"] = correct_phase

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

    # Get the actual value of the phase and time from df (ground truth)
    if match_condition.any():
        phase_true = int(df.loc[match_condition, "Phase_true"])
        time_start = int(df.loc[match_condition, "Phase_start_true"])
        time_end = int(df.loc[match_condition, "Phase_end_true"])
        correct_phase = calculate_if_correct(
            phase_true, phase, time_start, time_end, event_time)

        df.loc[match_condition, "bl_correct"] = correct_phase

# Save the updated DataFrame
name_new_game_path = datei_pfad.replace(".csv.xlsx", "_updated.csv.xlsx")
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

# Accuracy for Phase_rulebased
rulebased_correct = (df['rb_correct'] == 1).sum()
rulebased_accuracy = rulebased_correct / baseline_total

# Show the results
print(f"Accuracy für Phase_baseline: {baseline_accuracy:.4f}")
print(f"Accuracy für Phase_rulebased: {rulebased_accuracy:.4f}")

# Function to calculate the accuracy for each event type


# def calculate_accuracy_for_event_type(df: Any, event_type_column: Any,
#                                       phase_column: Any,
#                                       true_column: str = '
# Phase_true') -> Any:
#     # Find the accuracy for each event type
#     accuracy_per_event = df.groupby(event_type_column).apply(
#         lambda group: (group[true_column] ==
#                        group[phase_column]).sum() / len(group)
#     )
#     return accuracy_per_event

def calculate_accuracy_for_event_type(df: Any, event_type_column: Any,
                                      correct_column: Any) -> Any:
    # Find the accuracy for each event type
    accuracy_per_event = df.groupby(event_type_column).apply(
        lambda group: (group[correct_column] ==
                       1).sum() / len(group)
    )
    return accuracy_per_event


# # Calculate the accuracy for each event type
# baseline_accuracy_per_event = calculate_accuracy_for_event_type(
#     df, 'eID', 'Phase_baseline')
# rulebased_accuracy_per_event = calculate_accuracy_for_event_type(
#     df, 'eID', 'Phase_rulebased')

    # return accuracy_per_event


# Calculate the accuracy for each event type
baseline_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'bl_correct')
rulebased_accuracy_per_event = calculate_accuracy_for_event_type(
    df, 'eID', 'rb_correct')

# Show the results
print("Accuracy pro Event-Typ für Phase_baseline:")
print(baseline_accuracy_per_event)

print("\nAccuracy pro Event-Typ für Phase_rulebased:")
print(rulebased_accuracy_per_event)
