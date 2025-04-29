import pandas as pd

"""
This script processes event data from an Excel file and calculates
various statistics for each event type.
Author:
    @Annabelle Runge
Date:
    2025-04-29
"""

# List of event IDs we want to analyze
target_events = [
    'score_change',
    'seven_m_awarded',
    'shot_blocked',
    'shot_off_target',
    'shot_saved',
    'steal',
    'technical_ball_fault',
    'technical_rule_fault'
]

# Columns we want to calculate means for
algorithm_columns = [
    'none_correct',
    'bl_correct',
    'rb_correct',
    'pos_correct',
    'pos_rb_correct',
    'pos_cor_correct',
    'cost_correct',
    'cost_rb_correct',
    'cost_cor_correct'
]

try:
    # Read the Excel file with the full path
    file_path = (
        r"D:\Handball\HBL_Events\season_20_21\Datengrundlagen\progressed_excel"
        r"\Bergischer HC_HSG Nordhorn-Lingen_11.10.2020_20-21_updated.csv.xlsx"
    )
    df = pd.read_excel(file_path)

    # Initialize results dictionaries
    results = {}
    counts = {}
    sums = {}

    # Calculate means for each event type
    for event in target_events:
        # Filter rows for this event type
        event_data = df[df['eID'] == event]

        # Skip if no data found for this event
        if len(event_data) == 0:
            print(f"No data found for event: {event}")
            continue

        # Calculate means and store counts for each algorithm column
        means = {}
        event_counts = {}
        event_sums = {}

        for col in algorithm_columns:
            if col in event_data.columns:
                # Convert to numeric, ignoring errors
                numeric_data = pd.to_numeric(event_data[col], errors='coerce')

                # Calculate total count (excluding NaN)
                total_count = numeric_data.count()
                event_counts[col] = total_count

                # Calculate sum of ones (correct predictions)
                sum_ones = numeric_data.sum()
                event_sums[col] = sum_ones

                # Calculate mean
                mean_val = numeric_data.mean()
                means[col] = mean_val * 100 if not pd.isna(mean_val) else 0

        results[event] = means
        counts[event] = event_counts
        sums[event] = event_sums

    # Create DataFrames
    results_df = pd.DataFrame.from_dict(results, orient='index')
    counts_df = pd.DataFrame.from_dict(counts, orient='index')
    sums_df = pd.DataFrame.from_dict(sums, orient='index')

    # Round percentage values
    results_df = results_df.round(2)

    # Save to Excel with multiple sheets
    output_file = "event_type_analysis.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        results_df.to_excel(writer, sheet_name='Percentages')
        counts_df.to_excel(writer, sheet_name='Total Counts')
        sums_df.to_excel(writer, sheet_name='Sum of Ones')

    # Print results
    print("\nResults (percentages):")
    print("-" * 100)
    print(f"{'Event Type':<25} | " +
          " | ".join(f"{col:<12}" for col in algorithm_columns))
    print("-" * 100)

    for event, means in results.items():
        values = [f"{means.get(col, 0):.2f}%" for col in algorithm_columns]
        print(f"{event:<25} | " + " | ".join(f"{val:<12}" for val in values))

    print("\nTotal Counts:")
    print("-" * 100)
    for event, event_counts in counts.items():
        counts_values = [str(event_counts.get(col, 0))
                         for col in algorithm_columns]
        print(f"{event:<25} | " +
              " | ".join(f"{val:<12}" for val in counts_values))

    print("\nSum of Ones (Correct Predictions):")
    print("-" * 100)
    for event, event_sums in sums.items():
        sums_values = [str(event_sums.get(col, 0))
                       for col in algorithm_columns]
        print(f"{event:<25} | " + " | ".join(f"{val:<12}"
                                             for val in sums_values))

    print(f"\nResults have been saved to {output_file}")

except Exception as e:
    print(f"Error processing file: {str(e)}")
