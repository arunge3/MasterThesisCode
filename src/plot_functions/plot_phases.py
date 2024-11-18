import matplotlib
import matplotlib.pyplot as plt

import plot_functions.processing as processing

matplotlib.use("TkAgg", force=True)


def plot_phases(match_id: int) -> None:
    """
    Plots the phases of a handball match along with event markers.
    Args:
        match_id (int): The ID of the match.
    Returns:
        None
    This function performs the following steps:
    1. Loads paths and initial timestamps for the match.
    2. Converts event frame numbers to absolute timestamps.
    3. Loads positional data and phasse predictions.
    4. Calculates sequences of game phases.
    5. Defines positions and labels for each phase.
    6. Defines event colors based on categories.
    7. Initializes lists to hold x (time) and y (position) values for a
    continuous line.
    8. Fills in x_vals and y_vals for a continuous line.
    9. Creates the plot and adds event markers with labels from `type`.
    10. Customizes the plot and shows it.
    Note:
        The function assumes the existence of several helper functions
        and modules such as `helpFuctions`, `np`, `plt`, and `Code`.
    """

    events, team_info = processing.adjustTimestamp(match_id)
    sequences = processing.calculate_sequences(match_id)
    events, sequences = processing.synchronize_events(
        events, sequences, team_info)

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
        "score_change": "dodgerblue",
        "suspension": "purple",
        "suspension_over": "darkviolet",
        "technical_rule_fault": "gold",
        "technical_ball_fault": "orange",
        "steal": "limegreen",
        "shot_saved": "mediumblue",
        "shot_off_target": "crimson",
        "shot_blocked": "red",
        "seven_m_awarded": "deeppink",
        "seven_m_missed": "hotpink",
        "yellow_card": "yellow",
        "red_card": "darkred",
        "timeout": "cyan",
        "timeout_over": "cyan",
        "subsitution": "black",
        # Default for all other events
        "default": "grey",
    }
    # Initialize lists to hold x (time) and y (position) values for a
    # continuous line
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
    _, ax = plt.subplots(figsize=(14, 4))

    # Plot the continuous line
    ax.plot(x_vals, y_vals, color="black", linewidth=2)

    # Track labels to avoid duplicates in the legend
    added_labels = set()

    # Add event markers with labels from `type`
    for event in events:
        t_start = event["time"]
        event_type = event["type"]
        color = event_colors.get(event_type, event_colors["default"])
        # Find the y value on the continuous line for this event's time
        # (t_start)
        event_y = None
        for start, end, phase in sequences:
            if start <= t_start < end:
                event_y = phase_positions[phase]

                break
        # Plot event marker
        # ax.axvline(t_start, color="red", linestyle="--", linewidth=1)
        # Vertical line at event time
        if event_y is not None:
            ax.plot(
                t_start,
                event_y,
                "x",
                color=color,
                markersize=8,
                label=event_type if event_type not in added_labels else "",
            )
            print(t_start, event_y, event_type)
            added_labels.add(event_type)
    # Add legend
    ax.legend(title="Event Types", loc="upper right", bbox_to_anchor=(1.15, 1))

    # Customize the plot
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_yticks(sorted(set(phase_positions.values())))
    ax.set_yticklabels(
        [phase_labels[phase] for phase in sorted(phase_positions.keys())]
    )
    ax.set_xlabel("Timeframe")
    ax.set_title("Continuous Game phase Timeline")

    # Set x-axis limit to show only from 0 to 2000
    ax.set_xlim(6000, 50000)
    # Show plot
    plt.show()
