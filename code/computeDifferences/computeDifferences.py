import json
import os
import pandas as pd
import matplotlib.pyplot as plt

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
                print(f"Warning: Event without 'annotator', 't_start' or 'type' found in file {filename}.")
    return data_dict

# Directories containing the old and new JSONL files
old_jsonl_dir = r"D:\Handball\HBL_Events\season_20_21\EventJson"
new_jsonl_dir = r"D:\Handball\HBL_Synchronization\Annotationen"
output_dir_sum = r"D:\Handball\HBL_Events\season_20_21\EventDifference\Summary"
output_dir_det = r"D:\Handball\HBL_Events\season_20_21\EventDifference\Details"
output_dir_box = r"D:\Handball\HBL_Events\season_20_21\EventDifference\Boxplot"

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
            print(f"Warning: Not integer t_start values for key {event_key}")

# Create a DataFrame from the list of changes
df_changes = pd.DataFrame(changes_list)

# Filter out specific event types
excluded_events_boxplot = ["match_started", "period_start", "substitution", "suspension_over", "period_score","break_start","match_ended"]
df_filtered_boxplot = df_changes[~df_changes['event_type'].isin(excluded_events_boxplot)]

# Create a boxplot of the differences in timestamps by event type
plt.figure(figsize=(12, 6))
boxplot_data = [df_filtered_boxplot[df_filtered_boxplot['event_type'] == et]['difference'] for et in df_filtered_boxplot['event_type'].unique()]
plt.boxplot(boxplot_data, labels=df_filtered_boxplot['event_type'].unique(), showmeans=True)
plt.xlabel('Event Type')
plt.ylabel('Difference in t_start (new - old)')
plt.title('Boxplot of Differences in t_start by Event Type')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()

# Save the boxplot image
match_id = os.path.basename(old_file).split('_')[2]
boxplot_filename = os.path.join(output_dir_box, f'boxplot_differences_match_{match_id}.png')
plt.savefig(boxplot_filename)
plt.close() 

# Save adjustments in a CSV-File
csv_filename = os.path.join(output_dir_det, f'differences_details_match_{match_id}.csv')
df_changes.to_csv(csv_filename, index=False)

print(f"Boxplot saved here: {boxplot_filename}")
print(f"Calculations saved here: {csv_filename}")

# Calculation of summary_statistics just without "substitution" and "suspension_over"
excluded_events_summary = ["substitution", "suspension_over"]
df_filtered_summary = df_changes[~df_changes['event_type'].isin(excluded_events_summary)]

# Calculate mean and standard deviation for event-types
summary_stats = df_filtered_summary.groupby('event_type')['difference'].agg(['mean', 'std']).reset_index()

# Naming of columns
summary_stats.columns = ['event_type', 'average_difference', 'std_deviation']

# Calculate overall mean and standard deviation
overall_mean = df_filtered_summary['difference'].mean()
overall_std = df_filtered_summary['difference'].std()

# Overall statistics into a new DataFrame
overall_stats = pd.DataFrame({
    'event_type': ['overall'],
    'average_difference': [overall_mean],
    'std_deviation': [overall_std]
})

# Combine overall statistics with event type statistics
final_summary_stats = pd.concat([summary_stats, overall_stats], ignore_index=True)

# Save the summary statistics to a CSV file
summary_csv_filename = os.path.join(output_dir_sum, f'summary_statistics_match_{match_id}.csv')
final_summary_stats.to_csv(summary_csv_filename, index=False)

print(f"Summary saved here: {summary_csv_filename}")