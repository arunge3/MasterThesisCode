import copy
import json
import os
from pathlib import Path
from typing import Any, Dict


def calculate_rates(d: Dict[str, Any]) -> None:
    """
    Recalculate rates and percentages based on the underlying totals.
    Args:
        d: The dictionary containing the statistics.
    Returns:
        None
    """
    # Handle formation attack success rates - corrected path
    if ("Combined_Match_Statistics" in d and
        "original_statistics" in d["Combined_Match_Statistics"] and
        "formations" in d["Combined_Match_Statistics"]
        ["original_statistics"] and
        "attack_success_rate_per_formation" in
            d["Combined_Match_Statistics"]
            ["original_statistics"]["formations"]):

        formations = (d["Combined_Match_Statistics"]["original_statistics"]
                      ["formations"]["attack_success_rate_per_formation"])
        for period in formations.values():
            if "formation_attack_success_rates" in period:
                for formation_stats in (period
                                        ["formation_attack_success_rates"]
                                        .values()):
                    if ("total_shots" in formation_stats and
                            "goals" in formation_stats):
                        if formation_stats["total_shots"] > 0:
                            formation_stats["attack_success_rate"] = (
                                formation_stats["goals"] /
                                formation_stats["total_shots"] * 100
                            )
                        else:
                            formation_stats["attack_success_rate"] = 0.0

    # Handle success rates in phases - corrected path
    if ("Combined_Match_Statistics" in d and
        "original_statistics" in d["Combined_Match_Statistics"] and
            "phases" in d["Combined_Match_Statistics"]["original_statistics"]):

        phase_data = (d["Combined_Match_Statistics"]["original_statistics"]
                      ["phases"])
        if "Goal_success_rate_per_phase" in phase_data:
            phase_stats = phase_data["Goal_success_rate_per_phase"]
            if "event_stats" in phase_stats and "success_rates" in phase_stats:
                for team in ["home", "away"]:
                    event_stats = phase_stats["event_stats"][team]
                    success_rates = phase_stats["success_rates"][team]

                    for phase_type in ["position", "counter", "neutral"]:
                        if phase_type in event_stats:
                            total_attempts = event_stats[phase_type]["total"]
                            score_changes = event_stats[phase_type].get(
                                "score_change", 0)
                            seven_m_awarded = event_stats[phase_type].get(
                                "seven_m_awarded", 0)

                            if total_attempts > 0:
                                (success_rates[phase_type]
                                 ["goal_rate"]) = score_changes / \
                                    total_attempts
                                (success_rates[phase_type]
                                 ["successful_attack_rate"]) = (
                                    (score_changes + seven_m_awarded) /
                                    total_attempts
                                )
                            else:
                                (success_rates[phase_type]
                                 ["goal_rate"]) = 0.0
                                (success_rates[phase_type]
                                 ["successful_attack_rate"]) = 0.0

    # Handle goal rates in player counts
    if "Goal_Rate power_play and outnumbered attacks" in d:
        for team, stats in (d["Goal_Rate power_play and outnumbered attacks"]
                            .items()):
            team_data = (d["Combined_Match_Statistics"]
                         ["player_situation_analysis"][team])

            # Calculate full strength goal rate
            equal_strength = team_data["equal_strength_attacks"]
            if equal_strength["total_attempts"] > 0:
                stats["goal_rate_full"] = equal_strength["goals"] / \
                    equal_strength["total_attempts"]
            else:
                stats["goal_rate_full"] = 0.0

            # Calculate power play goal rate
            power_play = team_data["power_play_attacks"]
            if power_play["total_attempts"] > 0:
                stats["goal_rate_power_play"] = power_play["goals"] / \
                    power_play["total_attempts"]
            else:
                stats["goal_rate_power_play"] = 0.0

            # Calculate outnumbered goal rate
            outnumbered = team_data["outnumbered_attacks"]
            if outnumbered["total_attempts"] > 0:
                stats["goal_rate_outnumbered"] = outnumbered["goals"] / \
                    outnumbered["total_attempts"]
            else:
                stats["goal_rate_outnumbered"] = 0.0


def deep_sum_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]
                   ) -> Dict[str, Any]:
    """
    Recursively sum numeric values in nested dictionaries.
    Skip summing percentage/rate fields.
    Args:
        dict1: The first dictionary to sum.
        dict2: The second dictionary to sum.
    Returns:
        A dictionary with the summed values.
    """
    result = copy.deepcopy(dict1)

    # List of keys that represent rates/percentages that shouldn't be summed
    rate_keys = {"attack_success_rate", "goal_rate", "successful_attack_rate"}

    for key, value in dict2.items():
        if key in rate_keys:
            continue  # Skip summing rates
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = deep_sum_dicts(result[key], value)
        elif isinstance(value, (int, float)):
            result[key] += value

    return result


def calculate_averages(sum_dict: Dict[str, Any], file_count: int
                       ) -> Dict[str, Any]:
    """
    Calculate averages for all numeric values in the nested dictionary.
    Args:
        sum_dict: The dictionary containing the summed values.
        file_count: The number of files processed.
    Returns:
        A dictionary with the averaged values.
    """
    result = copy.deepcopy(sum_dict)

    def recursive_average(d: Dict[str, Any]) -> None:
        for key, value in d.items():
            if isinstance(value, dict):
                recursive_average(value)
            elif isinstance(value, (int, float)):
                d[key] = value / file_count

    recursive_average(result)
    return result


def aggregate_statistics(input_dir: str, output_dir: str) -> None:
    """
    Process all JSON files in the input directory and create
    summary statistics.

    Args:
        input_dir: Directory containing JSON files to process
        output_dir: Directory where output files will be saved
    Returns:
        None
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Initialize variables
    combined_stats: Dict[str, Any] = {}
    file_count = 0

    # Process all JSON files
    for file_path in Path(input_dir).glob('**/*.json'):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                if not combined_stats:
                    combined_stats = copy.deepcopy(data)
                else:
                    combined_stats = deep_sum_dicts(combined_stats, data)
                file_count += 1
            except json.JSONDecodeError:
                print(f"Error reading file: {file_path}")
                continue

    if file_count == 0:
        print("No valid JSON files found")
        return

    # Add file count to the summary
    combined_stats['total_files_processed'] = file_count

    # Calculate rates for the total statistics
    calculate_rates(combined_stats)

    # Save total sums
    with open(os.path.join(output_dir, 'total_statistics.json'), 'w') as f:
        json.dump(combined_stats, f, indent=4)

    # Calculate averages (including the rates)
    average_stats = calculate_averages(combined_stats, file_count)

    # Save averages
    with open(os.path.join(output_dir, 'average_statistics.json'), 'w') as f:
        json.dump(average_stats, f, indent=4)


# Example usage
if __name__ == "__main__":
    input_directory = "D:/Handball/HBL_Events/season_20_21/Analysis_results"
    output_directory = "D:/Handball/HBL_Events/season_20_21/Summary_Statistics"
    aggregate_statistics(input_directory, output_directory)
