import json
import os
from typing import Any

from matplotlib import pyplot as plt

import synchronization_approaches.pos_data_approach as pos_data_approach
import variables.data_variables as dv
from evaluation import sportanalysis
from help_functions.floodlight_code import (add_team_to_events,
                                            adjust_timestamp_baseline,
                                            calculate_event_stream,
                                            calculate_team_order)
from old_code import cost_function_approach
from plot_functions import processing
from plot_functions.plot_phases import berechne_phase_und_speichern_fl
from sport_analysis import sport_analysis_overall
from synchronization_approaches import cost_function_approach_2, rule_based
from synchronization_approaches.correction_extension import correct_events_fl


def approach_plot(match_id: int, approach: dv.Approach
                  = dv.Approach.RULE_BASED,
                  base_path: str = r"D:\Handball\HBL_Events\season_20_21"
                  ) -> None:
    """
    Plots the phases of a handball match along with event markers.
    Args:
        match_id (int): The ID of the match.
        approach (dv.Approach): The approach to use for synchronization.
        base_path (str): The base path to the data files.
    Returns:
        None
    """
    (events, sequences, datei_pfad) = (handle_approach(
        approach, processing.calculate_sequences(match_id),
        match_id, os.path.join(base_path, r"Datengrundlagen")))
    events = sportanalysis.evaluation_of_players_on_field(
        match_id, events, sequences)
    events = sportanalysis.evaluate_phase_events(events, sequences)
    events = sportanalysis.next_phase(events, sequences)
    plot_phases(events, sequences, datei_pfad, match_id, approach)
    if approach == dv.Approach.COST_BASED:

        events1, sequences = correct_events_fl(events, sequences)
        events1 = sportanalysis.evaluation_of_players_on_field(
            match_id, events1, sequences)
        events1 = sportanalysis.evaluate_phase_events(events1, sequences)
        datei_pfad = os.path.join(os.path.join(base_path, r"Datengrundlagen"),
                                  r"cost_based_cor",
                                  (str(match_id) + "_cost_based_cor_fl.csv"))
        plot_phases(events1, sequences, datei_pfad, match_id, approach)
        events2, sequences = rule_based.synchronize_events_fl_rule_based(
            events, sequences)
        datei_pfad = os.path.join(os.path.join(base_path, r"Datengrundlagen"),
                                  r"cost_based_rb",
                                  (str(match_id) + "_cost_based_rb_fl.csv"))
        events2 = sportanalysis.evaluation_of_players_on_field(
            match_id, events, sequences)
        events2 = sportanalysis.evaluate_phase_events(events2, sequences)
        plot_phases(events2, sequences, datei_pfad, match_id, approach)


def plot_phases(events: Any, sequences: list[tuple[int, int, int]],
                datei_pfad: str, match_id: int, approach: dv.Approach
                = dv.Approach.RULE_BASED,
                base_path: str = r"D:\Handball\HBL_Events\season_20_21"
                ) -> None:
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

    combined_results = sport_analysis_overall.create_combined_statistics(
        events, match_id)

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
    # Save analysis results to a JSON file
    analysis_results_path = os.path.join(
        base_path, r"Analysis_results",
        f"analysis_results_{match_id}_{approach.name}.json")
    with open(analysis_results_path, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=4)
    berechne_phase_und_speichern_fl(events, sequences, datei_pfad)
    # Add event markers with labels from `type`
    if hasattr(events, 'values'):
        for event in events.values:
            # Find the y value on the continuous line for this event's time
            event_y = None
            for start, end, phase in sequences:
                if start <= event[24] < end:
                    event_y = phase_positions[phase]

                    break
            if event_y is not None:
                ax.plot(
                    event[24],
                    event_y,
                    "x",
                    color=event_colors.get(event[0], event_colors["default"]),
                    markersize=8,
                    label=event[0] if event[0] not in added_labels else "",
                )
                added_labels.add(event[0])
        # Add legend
        ax.legend(title="Event Types", loc="upper right",
                  bbox_to_anchor=(1.15, 1))

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
    else:
        for event in events:
            # Find the y value on the continuous line for this event's time
            event_y = None
            for start, end, phase in sequences:

                if start <= event["time"] < end:
                    event_y = phase_positions[phase]

                    break
            if event_y is not None:
                ax.plot(
                    event["time"],
                    event_y,
                    "x",
                    color=event_colors.get(
                        event["type"], event_colors["default"]),
                    markersize=8,
                    label=(event["type"] if event["type"]
                           not in added_labels else ""),
                )
                added_labels.add(event["type"])
        # Add legend
        ax.legend(title="Event Types", loc="upper right",
                  bbox_to_anchor=(1.15, 1))

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
        # plt.show()


def handle_approach(approach: dv.Approach,
                    sequences: list[tuple[int, int, int]],
                    match_id: int, datengrundlage: str) -> (
                        tuple[Any, list[tuple[int, int, int]], str]):
    """
    Handles the approach for the event stream.
    Args:

        approach (dv.Approach): The approach to use for
        synchronization
        sequences (list[tuple[int, int, int]]): The sequences
        to use for synchronization
        match_id (int): The match ID to use for synchronization
        datengrundlage (str): The base path to the data files
    Returns:
        tuple[Any, list[tuple[int, int, int]], str]: A tuple
        containing the events,
        the sequences, and the datei_pfad.
    """
    # BASELINE NONE APPROACH
    if approach == dv.Approach.NONE:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        datei_pfad = os.path.join(
            datengrundlage, r"none", (str(match_id) + "_none_fl.csv"))

    # BASELINE MEAN APPROACH
    elif approach == dv.Approach.BASELINE:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = adjust_timestamp_baseline(events)

        datei_pfad = os.path.join(datengrundlage, r"baseline",
                                  (str(match_id) + "_bl_fl.csv"))

    # RULE BASED APPROACH
    elif approach == dv.Approach.RULE_BASED:
        (_, _, events) = calculate_event_stream(match_id)
        # print(events)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events, sequences = rule_based.synchronize_events_fl_rule_based(
            events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"rulebased",
                                  (str(match_id) + "_rb_fl.csv"))

    # POSITIONAL DATA APPROACH
    elif approach == dv.Approach.POS_DATA:
        (_, _, events) = calculate_event_stream(match_id)
        datei_pfad = os.path.join(datengrundlage, r"pos",
                                  (str(match_id) + "_pos_fl.csv"))
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = pos_data_approach.sync_event_data_pos_data(
            events, match_id)

    # POSITIONAL RB APPROACH
    elif approach == dv.Approach.POS_RB:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = pos_data_approach.sync_event_data_pos_data(
            events, match_id)

        events, sequences = rule_based.synchronize_events_fl_rule_based(
            events, sequences)
        datei_pfad = os.path.join(datengrundlage, r"pos_rb",
                                  (str(match_id) + "_pos_rb_fl.csv")
                                  )
    # POSITIONAL CORRECTION APPROACH
    elif approach == dv.Approach.POS_CORRECTION:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = pos_data_approach.sync_event_data_pos_data(
            events, match_id)
        events, sequences = correct_events_fl(events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"pos_cor",
                                  (str(match_id) + "_pos_cor_fl.csv"))

    # COST BASED APPROACH
    elif approach == dv.Approach.COST_BASED:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = cost_function_approach_2.main(match_id, events)
        # events = cost_function_approach.sync_events_cost_function(
        #     events, sequences, match_id)

        datei_pfad = os.path.join(datengrundlage, r"cost_based",
                                  (str(match_id) + "_cost_based_fl.csv"))

    # COST BASED CORRECTION APPROACH
    elif approach == dv.Approach.COST_BASED_COR:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)
        events = cost_function_approach.sync_events_cost_function(
            events, sequences, match_id)
        events, sequences = correct_events_fl(events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"cost_based_cor",
                                  (str(match_id) + "_cost_based_cor_fl.csv"))

    # COST BASED RB APPROACH
    elif approach == dv.Approach.COST_BASED_RB:
        (_, _, events) = calculate_event_stream(match_id)
        team_order = calculate_team_order(events)
        events = add_team_to_events(events, team_order)

        events = cost_function_approach.sync_events_cost_function(
            events, sequences, match_id)
        events, sequences = rule_based.synchronize_events_fl_rule_based(
            events, sequences)

        datei_pfad = os.path.join(datengrundlage, r"cost_based_rb",
                                  (str(match_id) + "_cost_based_rb_fl.csv"))

    # INVALID APPROACH
    else:
        raise ValueError("Invalid approach specified!")
    return events, sequences, datei_pfad
