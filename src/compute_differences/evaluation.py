import json
import os

import pandas as pd

# Read the files
base_path = r"D:\Handball\HBL_Events\season_20_21"
datengrundlage = r"Datengrundlagen"
base_path_grundlage = os.path.join(base_path, datengrundlage)
name_game_path = r"HSC 2000 Coburg_TBV Lemgo Lippe_01.10.2020_20-21.csv.xlsx"
datei_pfad = os.path.join(base_path_grundlage, name_game_path)
event_name = r"EventTimeline\sport_events_23400267_timeline.json"
event_path = os.path.join(base_path, event_name)
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
# Exrahe Phase from the clips column
df["Phase_true"] = df["clips"].str.split("_").str[2]

# Convert the Phase to numeric
df["Phase_true"] = pd.to_numeric(df["Phase_true"], errors="coerce")


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

# Save the updated DataFrame
name_new_game_path = datei_pfad.replace(".csv.xlsx", "_updated.csv.xlsx")
df.to_excel(name_new_game_path, index=False)
print("Excel-Datei wurde aktualisiert und gespeichert.")
