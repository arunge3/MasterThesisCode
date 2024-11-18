import json
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytz  # type: ignore
from floodlight import Code

import help_functions.reformatJson_Methods as helpFuctions
from existing_code.rolling_mode import rolling_mode

matplotlib.use("TkAgg", force=True)


def plot_phases(match_id: int, event_name: str) -> None:
    """
    Plots the phases of a handball match along with annotated events.
    Args:
        match_id (int): The ID of the match to plot.
        event_name (str): The name of the event file (without extension)
        containing annotations.
    Returns:
        None
    This function performs the following steps:
    1. Constructs file paths for phase predictions and event annotations
    based on the provided match ID and event name.
    2. Loads the first timestamp and offset for positional data.
    3. Reads event annotations from a JSONL file and converts event frame
    numbers to absolute timestamps.
    4. Loads positional data and phase predictions, and processes the
    predictions to find sequences of game phases.
    5. Defines positions for each phase and colors for different event
    categories.
    6. Plots a continuous line representing the game phases and adds markers
    for events with labels.
    Note:
        - The function assumes that the necessary helper functions
        (`helpFuctions.get_paths_by_match_id`,
          `helpFuctions.load_first_timestamp_and_offset`, `rolling_mode`,
          and `Code`) are defined elsewhere in the codebase.
        - The function uses the `matplotlib` library for plotting.
    """

    # Paths
    base_path = "D:\\Handball\\"
    season = "season_20_21"

    # Framerate of the video
    fps_video = 29.97
    _, _, _, positions_path, cut_h1, _, _, match = (
        helpFuctions.get_paths_by_match_id(match_id))
    phase_predictions_path = (
        f"{base_path}HBL_Slicing\\{season}\\{match}.csv.npy")
    event_path = (
        f"{base_path}HBL_Synchronization\\Annotationen\\{event_name}.jsonl")
    (
        first_time_pos_str,
        first_time_pos_unix,
        fps_positional,
    ) = helpFuctions.load_first_timestamp_position(positions_path)

    # Initialize an empty list to store events
    events = []

    # Read the JSONL file
    with open(event_path, "r") as file:
        for line in file:
            # Parse the JSON object from the line and append
            # it to the events list
            event = json.loads(line)
            events.append(event)

    # Match start timestamp
    print("match_start_datetime:", first_time_pos_str)

    # Timezone
    utc_timezone = pytz.utc

    # Timestamp of the first positional data converting to datetime
    positional_data_start_timestamp = first_time_pos_unix / 1000
    positional_data_start_date = datetime.fromtimestamp(
        positional_data_start_timestamp
    ).replace(tzinfo=utc_timezone)
    print("positional_data_start_date:", positional_data_start_date)

    # Convert event frame numbers to absolute timestamps
    events_with_timestamps = []
    for event in events:
        t_start = event["t_start"]
        event_time_seconds = (t_start - cut_h1) / fps_video
        event_absolute_timestamp = (
            positional_data_start_timestamp + event_time_seconds)
        event_timestamp_date = (datetime.fromtimestamp(
            event_absolute_timestamp).replace(tzinfo=utc_timezone))
        print("event_timestamp_date:", event_timestamp_date)
        event_timeframe = (
            event_timestamp_date - positional_data_start_date
        ).seconds * 20
        events_with_timestamps.append(
            [event_timeframe, event["labels"]["type"]])

    # Load positional data and phase predictions
    predictions = np.load(phase_predictions_path)
    predictions = rolling_mode(predictions, 101)

    slices = Code(
        predictions,
        "match_phases",
        {0: "inac", 1: "CATT-A", 2: "CATT-B", 3: "PATT-A", 4: "PATT-B"},
        fps_positional,
    )

    # get Sequences of the game phases
    sequences = slices.find_sequences(return_type="list")
    sequences = [x for x in sequences if x[1] - x[0] > slices.framerate]

    # Define positions for each phase
    phase_positions = {
        0: 2,  # (inac)
        1: 3,  # (CATT-A)
        2: 1,  # (CATT-B)
        3: 4,  # (PATT-A)
        4: 0,  # (PATT-B)
    }
    phase_labels = {2: "inac", 3: "CATT-A",
                    1: "CATT-B", 4: "PATT-A", 0: "PATT-B"}
    # Define event colors based on categories
    event_colors = {
        "score_change": "blue",
        "suspension": "purple",
        "suspension_over": "purple",
        "technical_rule_fault": "orange",
        "technical_ball_fault": "orange",
        "steal": "green",
        "shot_saved": "dodgerblue",
        "shot_off_target": "lightcoral",
        "shot_blocked": "lightcoral",
        "seven_m_awarded": "lightcoral",
        "seven_m_missed": "lightcoral",
        "yellow_card": "yellow",
        "red_card": "red",
        # Default for all other events
        "default": "grey",
    }
    # Initialize lists to hold x (time) and y (position) values
    # for a continuous line
    x_vals = []
    y_vals = []

    # Fill in x_vals and y_vals for a continuous line
    for start, end, phase in sequences:
        # Append start of phase
        x_vals.append(start)
        y_vals.append(phase_positions[phase])

        # Append end of phase
        x_vals.append(end)
        y_vals.append(phase_positions[phase])

    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 4))

    # Plot the continuous line
    ax.plot(x_vals, y_vals, color="black", linewidth=2)
    # Add event markers with labels from `type`
    for event in events_with_timestamps:
        t_start = event[0]
        event_type = event[1]
        color = event_colors.get(event_type, event_colors["default"])
        # Find the y value on the continuous line for this
        # event's time (t_start)
        event_y = None
        for start, end, phase in sequences:
            if start <= t_start < end:
                event_y = phase_positions[phase]
                break
        # Plot event marker
        # ax.axvline(t_start, color="red", linestyle="--", linewidth=1)
        # # Vertical line at event time
        if event_y is not None:
            ax.plot(t_start, event_y, "x", color=color, markersize=8)
            print(t_start, event_y, event_type)
            # ax.plot(t_start, event_y, 2, color="red")
            # # Marker at centerline for event
            ax.text(
                t_start + 0.1,
                event_y + 0.1,
                event_type,
                color=color,
                rotation=90,
                ha="right",
                va="bottom",
            )  # Label with event type

    # Customize the plot
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_yticks(sorted(set(phase_positions.values())))
    ax.set_yticklabels(
        [phase_labels[phase] for phase in sorted(phase_positions.keys())]
    )
    ax.set_xlabel("Timeframe")
    ax.set_title("Continuous Game phase Timeline")

    # Set x-axis limit to show only from 0 to 2000
    ax.set_xlim(0, 20000)
    # Show plot
    plt.show()
