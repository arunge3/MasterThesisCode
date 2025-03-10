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


def process_csv_file(df: pd.DataFrame, csv_df: pd.DataFrame,
                     phase_column: str, time_column: str,
                     correct_column: str) -> pd.DataFrame:
    """
    Process a CSV file and update the main DataFrame with phase,
    time, and correctness information.

    Args:
        df: Main DataFrame to update
        csv_df: DataFrame containing the CSV data
        phase_column: Name of the column to store phase information
        time_column: Name of the column to store time information
        correct_column: Name of the column to store correctness
        information
    """
    for _, row in csv_df.iterrows():
        event_id = row['event_id']
        event_time = int(row['time'])
        phase = int(row['phase'])

        match_condition = (df["Event_id"] == event_id)

        # Write the event_id to the DataFrame
        df.loc[match_condition, "Event_id"] = event_id
        df.loc[match_condition, phase_column] = phase
        df.loc[match_condition, time_column] = event_time

        # Check if there are any matching conditions
        if match_condition.any():
            # Get all matched rows for "Phase_true"
            matched_rows = df.loc[match_condition, "Phase_true"]

            # Determine which index to use based on number of matches
            phase_true_index = matched_rows.index[0 if len(
                matched_rows) == 1 else 1]

            # Use the index to fetch the corresponding values
            phase_true = int(df.loc[phase_true_index, "Phase_true"])
            time_start = int(df.loc[phase_true_index, "Phase_start_true"])
            time_end = int(df.loc[phase_true_index, "Phase_end_true"])

            # Perform phase correctness calculation
            correct_phase = calculate_if_correct(
                phase_true, phase, time_start, time_end, event_time
            )
            df.loc[match_condition, correct_column] = correct_phase

    return df


def calculate_model_accuracy(df: pd.DataFrame,
                             correct_column: str) -> float:
    """
    Calculate the accuracy for a specific model based on its
    correct column.

    Args:
        df: DataFrame containing the data
        correct_column: Name of the column containing correctness
        information

    Returns:
        float: Accuracy value
    """
    correct_count = (df[correct_column] == 1).sum()
    total = len(df)
    return correct_count / total if total > 0 else 0


def calculate_accuracy_for_event_type(df: Any, event_type_column: Any,
                                      correct_column: Any) -> Any:
    """
    Calculate accuracy for each event type.

    Args:
        df: DataFrame containing the data
        event_type_column: Column name for event types
        correct_column: Column name for correctness values

    Returns:
        Series: Accuracy per event type
    """
    # Find the accuracy for each event type
    accuracy_per_event = df.groupby(event_type_column).apply(
        lambda group: (group[correct_column] ==
                       1).sum() / len(group)
    )
    return accuracy_per_event


def calculate_accuracy_for_specific_events(df: pd.DataFrame,
                                           correct_column: str
                                           ) -> Any:
    """
    Calculate accuracy specifically for predefined handball events.

    Args:
        df: DataFrame containing the data
        correct_column: Column name for correctness values

    Returns:
        tuple: (overall accuracy for specified events, dict of accuracies
        per event type)
    """
    # Define the specific events we want to analyze
    specific_events = [
        "score_change", "shot_saved", "shot_off_target", "shot_blocked",
        "technical_rule_fault", "seven_m_awarded", "steal",
        "technical_ball_fault"
    ]

    # Filter DataFrame for specific events
    specific_events_df = df[df['eID'].isin(specific_events)]

    # Calculate overall accuracy for specific events
    correct_count = (specific_events_df[correct_column] == 1).sum()
    total_count = len(specific_events_df)
    overall_accuracy = correct_count / total_count if total_count > 0 else 0

    return overall_accuracy


def write_results_to_csv(output_path: str,
                         accuracy_data: list[tuple[str, str, float]],
                         event_type_accuracies: dict[Any, Any],
                         specific_events_accuracies:
                             dict[str, tuple[float, dict[str, float]]]
                         ) -> None:
    """
    Write accuracy results to a CSV file.

    Args:
        output_path: Path to the output CSV file
        accuracy_data: List of tuples containing (approach, event_type,
        accuracy)
        event_type_accuracies: Dictionary of event type accuracies per approach
        specific_events_accuracies: Dictionary of accuracies for specific
        events per approach
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)

        # Write header
        writer.writerow(["Approach", "Event Type", "Accuracy"])

        # Write overall accuracies
        for approach, event_type, accuracy in accuracy_data:
            writer.writerow([approach, event_type, f"{accuracy:.4f}"])

        # Write per-event-type accuracies
        for approach, accuracies in event_type_accuracies.items():
            for event, accuracy in accuracies.items():
                writer.writerow([approach, event, f"{accuracy:.4f}"])

        # Write specific events section
        writer.writerow([])  # Empty row for spacing
        writer.writerow(["Specific Events Accuracies"])
        writer.writerow(["Approach", "Event Type", "Accuracy"])

        for approach, overall_acc in specific_events_accuracies.items():
            # Write overall accuracy for specific events
            writer.writerow(
                [approach, "specific_events_overall", f"{overall_acc:.4f}"])

    print(f"Results saved to {output_path}")


def calculate_all_accuracies(directory: str,
                             output_file: str) -> None:
    """
    Calculate the average overall and event-type accuracies for
    each approach across all CSV files.

    :param directory: Path to the directory containing CSV files.
    :param output_file: Path to the output summary file.
    :return: Two dictionaries: overall accuracies and event-type
    accuracies.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Nested dict: {Approach: {Event Type: [accuracies]}}
    type_accuracies: dict[Any, Any] = defaultdict(lambda: defaultdict(list))
    # Iterate through all CSV files in the directory
    for file_name in os.listdir(directory):
        if (file_name.endswith(".csv") and
                file_name.startswith("detailed_results_")):
            file_path = os.path.join(directory, file_name)
            try:
                # Read the CSV file
                df = pd.read_csv(file_path)

                # Extract event-type accuracies
                if 'Event Type' in df.columns and 'Accuracy' in df.columns:
                    for _, row in df.iterrows():
                        approach = row['Approach']
                        event_type = row['Event Type']
                        # Convert accuracy string to float
                        try:
                            accuracy = float(row['Accuracy'])
                            type_accuracies[approach][event_type].append(
                                accuracy)
                        except ValueError:
                            print(
                                f"Warning: Could not convert accuracy value "
                                f"'{row['Accuracy']}' to float")
                            continue
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

    print(f"Summary results saved to {output_file}")


def initialize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialize all required columns in the DataFrame if they don't exist.

    Args:
        df: DataFrame to initialize

    Returns:
        DataFrame: The initialized DataFrame
    """
    columns_to_initialize = [
        "Event_id", "Phase_true", "Phase_start_true", "Phase_end_true",
        "Phase_None", "Phase_none_time", "none_correct",
        "Phase_baseline", "Phase_bl_time", "bl_correct",
        "Phase_rulebased", "Phase_rb_time", "rb_correct",
        "Phase_pos-based", "Phase_pos_time", "pos_correct",
        "Phase_pos_rb-based", "Phase_pos_rb_time", "pos_rb_correct",
        "Phase_pos_cor-based", "Phase_pos_cor_time", "pos_cor_correct",
        "Phase_cost-based", "cost_time", "cost_correct",
        "Phase_cost_based_rb-based", "cost_rb_time", "cost_rb_correct",
        "Phase_cost_cor-based", "cost_cor_time", "cost_cor_correct"
    ]

    for column in columns_to_initialize:
        if column not in df.columns:
            df[column] = None

    return df


def main(game_number: int, game_name: str) -> None:
    # Generate paths for the current game

    (excel_path, name_new_game_path, event_path, csv_bl_path,
     csv_rb_path, csv_none_path, csv_pos_path, csv_pos_rb_path,
     csv_pos_cor_path, csv_cost_path, csv_cost_cor_path,
     csv_cost_rb_path, output_path, directory_results, output_file_all) = (
         generate_paths(game_number, game_name))

    # Read and prepare the main DataFrame
    df = pd.read_excel(excel_path)  # Lesen der Excel Datei (True Values)
    with open(event_path, "r") as file:
        events_inital = json.load(file)

    events_inital = events_inital["timeline"]
    for idx, event in enumerate(events_inital):
        last_event = give_last_event_fl(events_inital, event["time"])
        if last_event is not None:
            last_event = last_event[1]
        if (event["type"] == "score_change" and last_event["type"] ==
                "seven_m_awarded"):
            events_inital[idx]["type"] = "seven_m_scored"
    # Adjust the data types
    df["eID"] = df["eID"].astype(str)
    df["minute"] = df["minute"].fillna(0).astype(int)
    df["second"] = df["second"].fillna(0).astype(int)
    df = df.dropna(subset=["clips"])

    # Initialize all required columns
    # Excel Datei mit allen Spalten für die Actual Values
    df = initialize_dataframe_columns(df)

    # Extract phase information from clips
    df["Phase_start_true"] = df["clips"].str.split("_").str[0]
    df["Phase_end_true"] = df["clips"].str.split("_").str[1]
    df["Phase_true"] = df["clips"].str.split("_").str[2]

    # Convert the Phase to numeric
    df["Phase_true"] = pd.to_numeric(df["Phase_true"], errors="coerce")

    # Read all CSV files
    df_csv_bl = pd.read_csv(csv_bl_path)
    df_csv_rb = pd.read_csv(csv_rb_path)
    df_csv_none = pd.read_csv(csv_none_path)
    df_csv_pos = pd.read_csv(csv_pos_path)
    df_csv_pos_rb = pd.read_csv(csv_pos_rb_path)
    df_csv_pos_cor = pd.read_csv(csv_pos_cor_path)
    df_csv_cost = pd.read_csv(csv_cost_path)
    df_csv_cost_cor = pd.read_csv(csv_cost_cor_path)
    df_csv_cost_rb = pd.read_csv(csv_cost_rb_path)

    # Map event IDs from the timeline to the DataFrame
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

    df["Event_id"] = df["Event_id"].fillna(0).astype(int)

    # Process all CSV files
    df = process_csv_file(df, df_csv_rb, "Phase_rulebased",
                          "Phase_rb_time", "rb_correct")
    df = process_csv_file(df, df_csv_pos, "Phase_pos-based",
                          "Phase_pos_time", "pos_correct")
    df = process_csv_file(df, df_csv_pos_rb, "Phase_pos_rb-based",
                          "Phase_pos_rb_time", "pos_rb_correct")
    df = process_csv_file(df, df_csv_none, "Phase_None",
                          "Phase_none_time", "none_correct")
    df = process_csv_file(df, df_csv_bl, "Phase_baseline",
                          "Phase_bl_time", "bl_correct")
    df = process_csv_file(df, df_csv_pos_cor, "Phase_pos_cor-based",
                          "Phase_pos_cor_time", "pos_cor_correct")
    df = process_csv_file(df, df_csv_cost, "Phase_cost-based",
                          "cost_time", "cost_correct")
    df = process_csv_file(df, df_csv_cost_cor, "Phase_cost_cor-based",
                          "cost_cor_time", "cost_cor_correct")
    df = process_csv_file(df, df_csv_cost_rb, "Phase_cost_based_rb-based",
                          "cost_rb_time", "cost_rb_correct")

    # Save the updated DataFrame
    os.makedirs(os.path.dirname(name_new_game_path), exist_ok=True)
    df.to_excel(name_new_game_path, index=False)
    print(f"Excel file updated and saved to {name_new_game_path}")

    # Calculate model accuracies
    baseline_accuracy = calculate_model_accuracy(df, 'bl_correct')
    none_accuracy = calculate_model_accuracy(df, 'none_correct')
    rulebased_accuracy = calculate_model_accuracy(df, 'rb_correct')
    pos_accuracy = calculate_model_accuracy(df, 'pos_correct')
    pos_rb_accuracy = calculate_model_accuracy(df, 'pos_rb_correct')
    pos_cor_accuracy = calculate_model_accuracy(df, 'pos_cor_correct')
    cost_accuracy = calculate_model_accuracy(df, 'cost_correct')
    cost_rb_accuracy = calculate_model_accuracy(df, 'cost_rb_correct')
    cost_cor_accuracy = calculate_model_accuracy(df, 'cost_cor_correct')

    # Calculate per-event-type accuracies
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

    # Prepare accuracy data for CSV output
    accuracy_data = [
        ("None", "all", none_accuracy),
        ("Baseline", "all", baseline_accuracy),
        ("Rulebased", "all", rulebased_accuracy),
        ("pos", "all", pos_accuracy),
        ("pos_RB", "all", pos_rb_accuracy),
        ("pos_COR", "all", pos_cor_accuracy),
        ("Cost", "all", cost_accuracy),
        ("Cost_RB", "all", cost_rb_accuracy),
        ("Cost_COR", "all", cost_cor_accuracy)
    ]

    # Prepare event type accuracies for CSV output
    event_type_accuracies = {
        "None": none_accuracy_per_event.to_dict(),
        "Baseline": baseline_accuracy_per_event.to_dict(),
        "Rulebased": rulebased_accuracy_per_event.to_dict(),
        "pos": pos_accuracy_per_event.to_dict(),
        "pos_RB": pos_rb_accuracy_per_event.to_dict(),
        "pos_COR": pos_cor_accuracy_per_event.to_dict(),
        "Cost": cost_accuracy_per_event.to_dict(),
        "Cost_RB": cost_rb_accuracy_per_event.to_dict(),
        "Cost_COR": cost_cor_accuracy_per_event.to_dict()
    }

    # Calculate accuracies for specific events
    specific_events_accuracies = {}
    specific_events_accuracies["None"] = (
        calculate_accuracy_for_specific_events(
            df, 'none_correct'))
    specific_events_accuracies["Baseline"] = (
        calculate_accuracy_for_specific_events(
            df, 'bl_correct'))
    specific_events_accuracies["Rulebased"] = (
        calculate_accuracy_for_specific_events(
            df, 'rb_correct'))
    specific_events_accuracies["pos"] = (
        calculate_accuracy_for_specific_events(
            df, 'pos_correct'))
    specific_events_accuracies["pos_RB"] = (
        calculate_accuracy_for_specific_events(
            df, 'pos_rb_correct'))
    specific_events_accuracies["pos_COR"] = (
        calculate_accuracy_for_specific_events(
            df, 'pos_cor_correct'))
    specific_events_accuracies["Cost"] = (
        calculate_accuracy_for_specific_events(
            df, 'cost_correct'))
    specific_events_accuracies["Cost_RB"] = (
        calculate_accuracy_for_specific_events(
            df, 'cost_rb_correct'))
    specific_events_accuracies["Cost_COR"] = (
        calculate_accuracy_for_specific_events(
            df, 'cost_cor_correct'))

    # Write detailed results to CSV with specific events accuracies
    write_results_to_csv(output_path, accuracy_data,
                         event_type_accuracies, specific_events_accuracies)

    # Calculate and write summary results
    calculate_all_accuracies(directory_results, output_file_all)

    print(f"Evaluation completed for game {game_number}: {game_name}")


def give_last_event_fl(events_inital: list[dict[str, Any]], time: int) -> Any:
    for event in enumerate(events_inital):
        if event[1]["time"] > time:
            return event
    return None


if __name__ == "__main__":
    main(23400311, "Füchse Berlin_SC DHFK Leipzig_11.10.2020_20-21")
