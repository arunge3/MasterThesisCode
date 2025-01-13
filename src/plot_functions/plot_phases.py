"""
This script demonstrates various functionalities of the `os` module
for interacting with the operating system.
"""
import os
from enum import Enum
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from plot_functions import processing

# Enum für die drei Wahlmöglichkeiten


class Approach(Enum):
    """
    Enum class representing different approaches for synchronizing.

    Attributes:
        RULE_BASED (str): Represents a rule-based approach.
        BASELINE (str): Represents a baseline approach.
        NONE (str): Represents no calculation.
        ML_BASED (str): Represents a machine learning-based approach.
    """
    RULE_BASED = "Rule-based Approach"
    BASELINE = "Baseline"
    NONE = "No Calcuation"
    ML_BASED = "Machine Learning Approach"


matplotlib.use("TkAgg", force=True)


def plot_phases(match_id: int, approach: Approach
                = Approach.RULE_BASED) -> None:
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
    events = []
    base_path = r"D:\Handball\HBL_Events\season_20_21"
    datengrundlage = r"Datengrundlagen"
    base_path_grundlage = os.path.join(base_path, datengrundlage)
    sequences = processing.calculate_sequences(match_id)

    if approach == Approach.RULE_BASED:
        events, team_info = processing.adjust_timestamp(match_id)
        events, sequences = processing.synchronize_events(
            events, sequences, team_info)
        new_name = str(match_id) + "_rb.csv"
        datei_pfad = os.path.join(base_path_grundlage, r"rulebased", new_name)
    # elif approach == Approach.ML_BASED:
    #     events, team_info = processing.adjustTimestamp(match_id)
    #     events, sequences = processing.synchronize_events_ml(
    #         events, sequences, team_info)
    #     new_name = str(match_id) + "_ml.csv"
    #     datei_pfad = os.path.join(base_path_grundlage, r"ml", new_name)
    elif approach == Approach.BASELINE:
        events, team_info = processing.adjust_timestamp_baseline(match_id)
        new_name = str(match_id) + "_bl.csv"
        datei_pfad = os.path.join(base_path_grundlage, r"baseline", new_name)
    elif approach == Approach.NONE:
        events, _ = processing.get_events(match_id)
        new_name = str(match_id) + "_none.csv"
        datei_pfad = os.path.join(base_path_grundlage, r"none", new_name)
    else:
        raise ValueError("Invalid approach specified!")
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

    berechne_phase_und_speichern(events, sequences, datei_pfad)
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


def berechne_phase_und_speichern_fl(events: list[Any],
                                    sequences: list[tuple[int, int, int]],
                                    dateipfad: str) -> None:
    """
    Berechnet die Phase für jedes Event basierend auf den gegebenen Sequenzen
    und speichert die Ergebnisse in einer CSV-Datei.
    Args:
        events (list[Any]): Eine Liste von Events, wobei jedes Event eine Liste
        oder ein Tupel mit verschiedenen Attributen ist.
        sequences (list[tuple[int, int, int]]): Eine Liste von Tupeln, die die
        Start- und Endzeiten sowie die zugehörige Phase enthalten.
        dateipfad (str): Der Dateipfad, unter dem die CSV-Datei gespeichert
        werden soll.
    Returns:
        None
    """
    # Erstelle eine Liste, um die Event-Daten zu speichern
    event_data = []

    # Durchlaufe jedes Event
    for event in events:
        event_id = event[11]
        event_type = event[0]
        event_time = event[22]

        # Phase berechnen
        phase = None
        for start, end, ph in sequences:
            if start <= event_time < end:
                phase = ph
                break

        # Event-Daten hinzufügen
        if phase is not None:
            event_data.append({
                "event_id": event_id,
                "phase": phase,
                "type": event_type,
                "time": event_time
            })

    # DataFrame erstellen
    df = pd.DataFrame(event_data)

    # Speichern in eine CSV-Datei (oder Excel)
    # Ändere dies zu .to_excel für Excel-Datei
    df.to_csv(dateipfad, index=False)
    print(f"Die Datei wurde unter {dateipfad} gespeichert.")


def berechne_phase_und_speichern(events: list[Any],
                                 sequences: list[tuple[int, int, int]],
                                 dateipfad: str) -> None:
    """
    Berechnet die Phase für jedes Event basierend auf den gegebenen
    Sequenzen und speichert die Ergebnisse in einer CSV-Datei.
    Args:
    events (list[Any]): Eine Liste von Events, wobei jedes Event ein
    Dictionary mit den Schlüsseln "id", "type" und "time" ist.
    sequences (list[tuple[int, int, int]]): Eine Liste von Tupeln,
    die die Start- und Endzeiten sowie die Phaseninformationen enthalten.
    dateipfad (str): Der Dateipfad, unter dem die CSV-Datei gespeichert
    werden soll.

    Returns:
    None
    """

    # Erstelle eine Liste, um die Event-Daten zu speichern
    event_data = []

    # Durchlaufe jedes Event
    for event in events:
        event_id = event["id"]
        event_type = event["type"]
        event_time = event["time"]

        # Phase berechnen
        phase = None
        for start, end, ph in sequences:
            if start <= event_time < end:
                phase = ph
                break

        # Event-Daten hinzufügen
        if phase is not None:
            event_data.append({
                "event_id": event_id,
                "phase": phase,
                "type": event_type,
                "time": event_time
            })

    # DataFrame erstellen
    df = pd.DataFrame(event_data)

    # Speichern in eine CSV-Datei (oder Excel)
    # Ändere dies zu .to_excel für Excel-Datei
    df.to_csv(dateipfad, index=False)
    print(f"Die Datei wurde unter {dateipfad} gespeichert.")


def plot_events(match_id: int) -> None:
    """
    Plots the timeline of events for a given match.
    Parameters:
    match_id (int): The ID of the match for which events are
    to be plotted.
    The function retrieves events associated with the given
    match ID, assigns colors to different event types,
    and plots these events on a timeline. Each event is
    represented by a marker on the plot, with different
    colors indicating different types of events. A legend is
    added to the plot to describe the event types.

    Event Types and their Colors:
    - score_change: dodgerblue
    - suspension: purple
    - suspension_over: darkviolet
    - technical_rule_fault: gold
    - technical_ball_fault: orange
    - steal: limegreen
    - shot_saved: mediumblue
    - shot_off_target: crimson
    - shot_blocked: red
    - seven_m_awarded: deeppink
    - seven_m_missed: hotpink
    - yellow_card: yellow
    - red_card: darkred
    - timeout: cyan
    - timeout_over: cyan
    - subsitution: black
    - default: grey (for all other events)
    The plot is displayed with a single y-level for all
    events, and the x-axis represents the timeframe.
    """

    events, _ = processing.adjust_timestamp(match_id)
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

    # Initialize the plot
    _, ax = plt.subplots(figsize=(14, 4))

    # Track labels to avoid duplicates in the legend
    added_labels = set()

    # Add event markers
    for event in events:
        t_start = event["time"]
        event_type = event["type"]
        color = event_colors.get(event_type, event_colors["default"])

        # Plot event marker
        ax.plot(
            t_start,
            1,  # All events on a single y-level
            "x",
            color=color,
            markersize=8,
            label=event_type if event_type not in added_labels else "",
        )
        added_labels.add(event_type)

    # Add legend
    ax.legend(title="Event Types", loc="upper right", bbox_to_anchor=(1.15, 1))

    # Customize the plot
    ax.axhline(1, color="grey", linewidth=0.5,
               linestyle="")  # Baseline for events
    ax.set_yticks([1])  # Single y-tick
    ax.set_yticklabels(["Events"])  # Label for y-axis
    ax.set_xlabel("Timeframe")
    ax.set_title("Event Timeline")

    # Add some padding around the range
    ax.set_xlim(6000, 50000)

    # Show plot
    plt.show()
