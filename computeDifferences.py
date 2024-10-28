import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

"""
This script compares event timestamps from two JSONL files and generates statistical summaries and visualizations.
Functions:
    load_jsonl_as_dict(filename):
        Loads a JSONL file and returns a dictionary of events keyed by (annotator, event_type).
Variables:
    old_jsonl_dir (str): Directory containing the old JSONL files.
    new_jsonl_dir (str): Directory containing the new JSONL files.
    output_dir (str): Directory to save the output files.
    old_file (str): Path to the old JSONL file.
    new_file (str): Path to the new JSONL file.
    old_data (dict): Dictionary of events from the old JSONL file.
    new_data (dict): Dictionary of events from the new JSONL file.
    changes_list (list): List of dictionaries containing differences in event timestamps.
    df_changes (DataFrame): DataFrame containing the changes in event timestamps.
    df_filtered (DataFrame): Filtered DataFrame excluding specific event types.
    boxplot_filename (str): Path to save the boxplot image.
    csv_filename (str): Path to save the detailed differences CSV file.
    summary_stats (DataFrame): DataFrame containing summary statistics for each event type.
    overall_mean (float): Overall mean difference in timestamps.
    overall_std (float): Overall standard deviation of differences in timestamps.
    overall_stats (DataFrame): DataFrame containing overall summary statistics.
    final_summary_stats (DataFrame): DataFrame containing both event type-specific and overall summary statistics.
    summary_csv_filename (str): Path to save the summary statistics CSV file.
Outputs:
    - Boxplot image showing differences in event timestamps by event type.
    - CSV file with detailed differences in event timestamps.
    - CSV file with summary statistics of differences in event timestamps.
"""

def load_jsonl_as_dict(filename):
    """
    Loads events from a JSONL file and returns them as a dictionary.
    Each line in the JSONL file should represent a JSON object with the following structure:
    {
        "annotator": <annotator_name>,
        "t_start": <start_time>,
        "labels": {
            "type": <event_type>
        },
        ...
    }
    The function will use the combination of 'annotator' and 'type' as the key for the dictionary.
    Args:
        filename (str): The path to the JSONL file to be loaded.
    Returns:
        dict: A dictionary where the keys are tuples of (annotator, event_type) and the values are the corresponding event objects.
    Raises:
        FileNotFoundError: If the file specified by filename does not exist.
        json.JSONDecodeError: If a line in the file is not valid JSON.
    Warns:
        Prints a warning message if an event does not contain 'annotator', 't_start', or 'type'.
    """
    data_dict = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            event = json.loads(line.strip())
            annotator = event.get("annotator")
            t_start = event.get("t_start")
            event_type = event['labels'].get('type')
            
            if annotator and t_start is not None and event_type:
                event_key = (annotator, event_type)
                data_dict[event_key] = event
            else:
                print(f"Warnung: Event ohne 'annotator', 't_start' oder 'type' in Datei {filename} gefunden.")
    return data_dict

# Directories containing the old and new JSONL files
old_jsonl_dir = r"D:\Handball\HBL_Events\season_20_21\EventJson"
new_jsonl_dir = r"D:\Handball\HBL_Synchronization\Annotationen"
output_dir = r"D:\Handball\HBL_Events\season_20_21\EventDifference"

# Paths to the old and new JSONL files
old_file = os.path.join(old_jsonl_dir, "sport_events_23400321_timeline_reformatted.jsonl")
new_file = os.path.join(new_jsonl_dir, "241027-091504_2020-10-15_754549_rhein-neckar_loewen-sc_dhfk_leipzig-720p-3000kbps.jsonl")

# Load the events from the old and new JSONL files
old_data = load_jsonl_as_dict(old_file)
new_data = load_jsonl_as_dict(new_file)

# Compare the timestamps of events in the old and new JSONL files
changes_list = []
for event_key in old_data.keys():
    if event_key in new_data:
        old_t_start = old_data[event_key].get("t_start")
        new_t_start = new_data[event_key].get("t_start")
        
        # Only consider events with integer t_start values
        if isinstance(old_t_start, int) and isinstance(new_t_start, int):
           
            # Calculate the difference in timestamps
            diff = new_t_start - old_t_start
            event_type = old_data[event_key]['labels']['type']
            changes_list.append({
                'annotator': event_key[0],  
                'event_type': event_type,     
                'old_t_start': old_t_start,   
                'new_t_start': new_t_start,   
                'difference': diff
            })
        else:
            print(f"Warnung: Nicht-integer t_start-Werte für Schlüssel {event_key}")

# Create a DataFrame from the list of changes
df_changes = pd.DataFrame(changes_list)

# Filter out specific event types
df_filtered = df_changes[~df_changes['event_type'].isin(["match_started", "period_start"])]

# Create a boxplot of the differences in timestamps by event type
plt.figure(figsize=(12, 6))
boxplot_data = [df_filtered[df_filtered['event_type'] == et]['difference'] for et in df_filtered['event_type'].unique()]
plt.boxplot(boxplot_data, labels=df_filtered['event_type'].unique(), showmeans=True)
plt.xlabel('Event Type')
plt.ylabel('Differenz in t_start (neu - alt)')
plt.title('Differenzen der t_start-Werte (neu - alt) nach Event Type')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()

# Save the boxplot image
match_id = os.path.basename(old_file).split('_')[2]
boxplot_filename = os.path.join(output_dir, f'boxplot_differences_match_{match_id}.png')
plt.savefig(boxplot_filename)
plt.close() 

# Save the detailed differences to a CSV file
csv_filename = os.path.join(output_dir, f'differences_details_match_{match_id}.csv')
df_filtered.to_csv(csv_filename, index=False)

# Calculate summary statistics for each event type and overall
summary_stats = df_filtered.groupby('event_type')['difference'].agg(['mean', 'std']).reset_index()
summary_stats.columns = ['event_type', 'average_difference', 'std_deviation']
overall_mean = df_filtered['difference'].mean()
overall_std = df_filtered['difference'].std()

overall_stats = pd.DataFrame({
    'event_type': ['overall'],
    'average_difference': [overall_mean],
    'std_deviation': [overall_std]
})

# Combine the event type-specific and overall summary statistics
final_summary_stats = pd.concat([summary_stats, overall_stats], ignore_index=True)
summary_csv_filename = os.path.join(output_dir, f'summary_statistics_match_{match_id}.csv')
final_summary_stats.to_csv(summary_csv_filename, index=False)

# Print the paths to the output files
print(f"Zusammenfassung der Statistiken (inkl. Gesamt) gespeichert unter: {summary_csv_filename}")
print(f"Boxplot gespeichert unter: {boxplot_filename}")
print(f"Werte gespeichert unter: {csv_filename}")
