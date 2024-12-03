import os

import matplotlib.pyplot as plt
import pandas as pd

"""
This script processes event data from multiple CSV files, computes statistical
summaries, and generates visualizations.
Modules:
    os: Provides a way of using operating system dependent functionality.
    pandas: Library for data manipulation and analysis.
    matplotlib.pyplot: Library for creating static, animated, and interactive
    visualizations.
Constants:
    details_dir (str): Directory containing the event details CSV files.
    output_dir_sum (str): Directory to save the summary statistics CSV file.
    output_dir_box (str): Directory to save the boxplot image file.
Variables:
    all_events_data (DataFrame): DataFrame to store concatenated event data
    from all CSV files.
    excluded_events_boxplot (list): List of event types to exclude from the
    boxplot.
    df_filtered_boxplot (DataFrame): DataFrame containing filtered event data
    for the boxplot.
    boxplot_data (list): List of series containing 'difference' values for each
    event type.
    boxplot_filename (str): Path to save the boxplot image file.
    summary_stats_all_games (DataFrame): DataFrame containing mean and standard
    deviation of 'difference' for each event type.
    overall_mean (float): Overall mean of 'difference' across all events.
    overall_std (float): Overall standard deviation of 'difference' across all
    events.
    overall_stats (DataFrame): DataFrame containing overall mean and standard
    deviation.
    final_summary_stats_all_games (DataFrame): DataFrame containing combined
    summary statistics for each event type and overall.
    summary_filename (str): Path to save the summary statistics CSV file.
Functions:
    None
Execution:
    1. Reads and concatenates event data from CSV files in the details_dir.
    2. Filters out specified event types for the boxplot.
    3. Generates and saves a boxplot of 'difference' values by event type.
    4. Computes and saves summary statistics (mean and standard deviation)
    of 'difference'
    for each event type and overall.
"""
import matplotlib

matplotlib.use("Agg")  # Verwenden eines nicht-interaktiven Backends

# Input directories and output directories
details_dir = r"D:\Handball\HBL_Events\season_20_21\EventDifference\Details"
output_dir_sum = r"D:\Handball\HBL_Events\season_20_21\EventDifference\Summary"
output_dir_box = r"D:\Handball\HBL_Events\season_20_21\EventDifference\Boxplot"

# Concatenate all event data from CSV files
all_events_data = pd.DataFrame()
for file in os.listdir(details_dir):
    if file.endswith(".csv"):
        file_path = os.path.join(details_dir, file)
        df = pd.read_csv(file_path)
        all_events_data = pd.concat([all_events_data, df], ignore_index=True)

# Filter out specific event types for the boxplot
excluded_events_boxplot = [
    "match_started",
    "period_start",
    "substitution",
    "suspension_over",
    "period_score",
    "break_start",
    "match_ended",
]
df_filtered_boxplot = all_events_data[
    ~all_events_data["event_type"].isin(excluded_events_boxplot)
]

# Generate and save boxplot of 'difference' values by event type
plt.figure(figsize=(14, 7))
boxplot_data = [
    df_filtered_boxplot[df_filtered_boxplot["event_type"] == et]["difference"]
    for et in df_filtered_boxplot["event_type"].unique()
]
plt.boxplot(
    boxplot_data, tick_labels=df_filtered_boxplot["event_type"].unique(),
    showmeans=True
)
plt.xlabel("Event Type")
plt.ylabel("Difference in t_start (new - old)")
plt.title("Boxplot of Differences in t_start Across All Games by Event Type")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()

boxplot_filename = os.path.join(
    output_dir_box, "boxplot_differences_all_games.png")
plt.savefig(boxplot_filename)
plt.close()
print(f"Boxplot saved for all events here: {boxplot_filename}")

# Compute summary statistics for each event type and overall
summary_stats_all_games = (
    all_events_data.groupby("event_type")["difference"]
    .agg(["mean", "std"])
    .reset_index()
)
overall_mean = all_events_data["difference"].mean()
overall_std = all_events_data["difference"].std()

overall_stats = pd.DataFrame(
    {"event_type": ["overall"], "mean": [overall_mean], "std": [overall_std]}
)
final_summary_stats_all_games = pd.concat(
    [summary_stats_all_games, overall_stats], ignore_index=True
)

summary_filename = os.path.join(
    output_dir_sum, "summary_statistics_all_games.csv")
final_summary_stats_all_games.to_csv(summary_filename, index=False)
print(f"Summary of Calculations for all events saved here: {summary_filename}")


# # Boxplot ohne Ausreißer anzeigen
# plt.boxplot(data, showfliers=False)
# plt.title("Boxplot ohne Ausreißer (showfliers=False)")
# plt.show()
