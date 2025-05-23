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
        datengrundlage, r"baseline", f"{number}_bl_fl.csv")
    csv_rb_path = os.path.join(
        datengrundlage, r"rulebased", f"{number}_rb_fl.csv")

    csv_none_path = os.path.join(
        datengrundlage, r"none", f"{number}_none_fl.csv")
    csv_pos_path = os.path.join(
        datengrundlage, r"pos", f"{number}_pos_fl.csv")

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
        datengrundlage, r"results_some", f"detailed_results_{number}.csv")
    # Directory containing the CSV files

    directory_results = os.path.join(datengrundlage, r"results_some")
    # Save results to CSV
    output_file_all = os.path.join(datengrundlage,
                                   r"results_summary_some.csv")

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


def initialize_dataframe(excel_path: str, event_path: str) -> pd.DataFrame:
    """
    Initialisiert und bereitet den DataFrame vor.

    Args:
        excel_path: Pfad zur Excel-Datei
        event_path: Pfad zur Event-JSON-Datei

    Returns:
        pd.DataFrame: Initialisierter und vorbereiteter DataFrame
    """
    df = pd.read_excel(excel_path)
    with open(event_path, "r") as file:
        events_inital = json.load(file)

    events_inital = events_inital["timeline"]

    # Datentypen anpassen
    df["eID"] = df["eID"].astype(str)
    df["minute"] = df["minute"].fillna(0).astype(int)
    df["second"] = df["second"].fillna(0).astype(int)
    df = df.dropna(subset=["clips"])

    # Neue Spalten definieren
    neue_spalten = [
        "Event_id", "Phase_true", "Phase_start_true", "Phase_end_true",
        "Phase_None", "Phase_none_time", "none_correct",
        "Phase_baseline", "Phase_bl_time", "bl_correct",
        "Phase_rulebased", "Phase_rb_time", "rb_correct",
        "Phase_pos-based", "Phase_pos_time", "pos_correct",
        "Phase_pos_rb-based", "Phase_pos_rb_time", "pos_rb_correct",
        "Phase_pos_cor-based", "Phase_pos_cor_time", "pos_cor_correct",
        "Phase_cost-based", "cost_time", "cost_correct",
        "Phase_cost_based_rb-based", "cost_rb_time", "cost_rb_correct"
    ]

    # Spalten initialisieren falls nicht vorhanden
    for spalte in neue_spalten:
        if spalte not in df.columns:
            df[spalte] = None

    # Phasen aus der clips-Spalte extrahieren
    df["Phase_start_true"] = df["clips"].str.split("_").str[0]
    df["Phase_end_true"] = df["clips"].str.split("_").str[1]
    df["Phase_true"] = df["clips"].str.split("_").str[2]

    # Phase zu numerisch konvertieren
    df["Phase_true"] = pd.to_numeric(df["Phase_true"], errors="coerce")

    return events_inital, df


def process_csv_data(df: pd.DataFrame, csv_df: pd.DataFrame,
                     method_name: str
                     ) -> pd.DataFrame:
    """
    Verarbeitet CSV-Daten für verschiedene Methoden und aktualisiert
    den DataFrame.

    Args:
        df: Haupt-DataFrame mit den Ground-Truth-Daten
        csv_df: DataFrame mit den Vorhersagen einer bestimmten Methode
        method_name: Name der Methode (z.B. 'rb' für regelbasiert)
    """
    for _, row in csv_df.iterrows():
        event_id = row['event_id']
        event_time = int(row['time'])
        phase = int(row['phase'])
        match_condition = (df["Event_id"] == event_id)

        # Spalten-Namen basierend auf method_name
        phase_col = f"Phase_{method_name}"
        time_col = f"Phase_{method_name}_time" if (method_name != "cost"
                                                   )else f"{method_name}_time"
        correct_col = f"{method_name}_correct"

        # DataFrame aktualisieren
        df.loc[match_condition, "Event_id"] = event_id
        df.loc[match_condition, phase_col] = phase
        df.loc[match_condition, time_col] = event_time

        if match_condition.any():
            matched_rows = df.loc[match_condition, "Phase_true"]
            idx = 0 if len(matched_rows) == 1 else 1

            phase_true = int(df.loc[match_condition, "Phase_true"].values[idx])
            time_start = int(
                df.loc[match_condition, "Phase_start_true"].values[idx])
            time_end = int(
                df.loc[match_condition, "Phase_end_true"].values[idx])

            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time)
            df.loc[match_condition, correct_col] = correct_phase

    return df


def evaluation(matchid: int, name_match: str) -> None:

    (excel_path, name_new_game_path, event_path, csv_bl_path,
     csv_rb_path, csv_none_path, csv_pos_path, csv_pos_rb_path,
     csv_pos_cor_path, csv_cost_path, csv_cost_cor_path,
     csv_cost_rb_path, output_path, directory_results, output_file_all
     ) = (generate_paths(matchid, name_match))

    events_inital, df = initialize_dataframe(excel_path, event_path)

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
            print(match_condition)

            print(df["eID"] == event_type)
            print(df["minute"] == (event_minutes))
            print(df["second"] == (event_seconds))
        else:
            match_condition = ((df["eID"] == event_type))

        # Write the event_id to the DataFrame
        df.loc[match_condition, "Event_id"] = event_id

    df["Event_id"] = df["Event_id"].fillna(0).astype(
        int)

    # CSV-Dateien und ihre Methoden-Namen
    csv_files = {
        'rulebased': (df_csv_rb, 'rb_time'),
        'pos': (df_csv_pos, 'pos_time'),
        'pos_rb': (df_csv_pos_rb, 'pos_rb_time'),
        'none': (df_csv_none, 'None'),
        'baseline': (df_csv_bl, 'baseline'),
        'pos_cor': (df_csv_pos_cor, 'pos_cor_time'),
        'cost': (df_csv_cost, 'cost-based'),
        'cost_cor': (df_csv_cost_cor, 'cost_cor-based'),
        'cost_rb': (df_csv_cost_rb, 'cost_based_rb-based')
    }

    # Verarbeite alle CSV-Dateien
    for csv_df, method_name in csv_files.values():
        df = process_csv_data(df, csv_df, method_name)

    df.to_excel(name_new_game_path, index=False)
    print("Excel-Datei wurde aktualisiert und gespeichert.")

    # Konstanten definieren
    RELEVANT_EVENTS = [
        "score_change",
        "shot_saved",
        "shot_blocked",
        "seven_m_awarded",
        "shot_off_target",
        "technical_ball_fault",
        "technical_rule_fault",
        "steal"
    ]

    APPROACHES = [
        ("None", "none_correct"),
        ("Baseline", "bl_correct"),
        ("Rulebased", "rb_correct"),
        ("pos", "pos_correct"),
        ("pos_RB", "pos_rb_correct"),
        ("pos_COR", "pos_cor_correct"),
        ("Cost", "cost_correct"),
        ("Cost_RB", "cost_rb_correct"),
        ("Cost_COR", "cost_cor-based_correct")
    ]

    def calculate_accuracy_for_event_type(df: pd.DataFrame,
                                          event_type_column: str,
                                          correct_column: str) -> pd.Series:
        """
        Berechnet die Genauigkeit pro Event-Typ für die gegebenen Daten.

        Args:
            df: DataFrame mit den Ereignisdaten
            event_type_column: Name der Spalte mit Event-Typen
            correct_column: Name der Spalte mit Korrektheitswerten

        Returns:
            pd.Series mit Genauigkeiten pro Event-Typ
        """
        df_filtered = df[df[event_type_column].isin(RELEVANT_EVENTS)]
        return df_filtered.groupby(event_type_column)[correct_column].mean()

    # Relevante Events filtern
    df_relevant = df[df['eID'].isin(RELEVANT_EVENTS)]
    # baseline_total = len(df_relevant)

    # Genauigkeiten berechnen
    accuracies = {}
    accuracy_per_events = {}

    for approach_name, correct_column in APPROACHES:
        # Gesamtgenauigkeit
        accuracies[approach_name] = (df_relevant[correct_column] == 1).mean()

        # Event-spezifische Genauigkeit
        accuracy_per_events[approach_name] = calculate_accuracy_for_event_type(
            df, 'eID', correct_column)

    # Ergebnisse in CSV schreiben
    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Approach", "Event Type", "Accuracy"])

        # Gesamtgenauigkeiten schreiben
        for approach_name in accuracies:
            writer.writerow([
                approach_name,
                "all",
                f"{accuracies[approach_name]:.4f}"
            ])

        # Event-spezifische Genauigkeiten schreiben
        for approach_name, accuracies_per_event in accuracy_per_events.items():
            for event, accuracy in accuracies_per_event.items():
                writer.writerow([approach_name, event, f"{accuracy:.4f}"])

    print(f"Ergebnisse wurden in {output_path} gespeichert")
    calculate_all_accuracies(directory_results, output_file_all)


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


evaluation(23400275, "Rhein-Neckar Löwen_TVB Stuttgart_04.10.2020_20-21")
evaluation(23400263, "TSV GWD Minden_TSV Hannover-Burgdorf_01.10.2020_20-21")
evaluation(23400307, "HSG Wetzlar_THW Kiel_10.10.2020_20-21")
evaluation(23400277, "HSG Wetzlar_SG Flensburg-Handewitt_04.10.2020_20-21")
evaluation(23400267, "HSC 2000 Coburg_TBV Lemgo Lippe_01.10.2020_20-21")
evaluation(23400303, "TSV Hannover-Burgdorf_HSC 2000 Coburg_08.10.2020_20-21")
evaluation(23400319, "Bergischer HC_HSG Nordhorn-Lingen_11.10.2020_20-21")
evaluation(23400315, "TUSEM Essen_Rhein-Neckar Löwen_11.10.2020_20-21")
evaluation(23400321, "Rhein-Neckar Löwen_SC DHFK Leipzig_15.10.2020_20-21")
evaluation(23400311, "Füchse Berlin_SC DHFK Leipzig_11.10.2020_20-21")
