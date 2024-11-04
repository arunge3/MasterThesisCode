import matplotlib.pyplot as plt
from floodlight.io.kinexon import read_position_data_csv
from floodlight import Code
from floodlight.core import pitch
import numpy as np
from rolling_mode import rolling_mode
import matplotlib
matplotlib.use('TkAgg',force=True)

print("Switched to:",matplotlib.get_backend())
base_path = "D:\\Handball\\"
season = "season_20_21"  # season of the match
match = "Bergischer HC_Die Eulen Ludwigshafen_16.12.2020_20-21"  # name of the match
path_positions = "D:\\Handball\\HBL_Positions\\21-22\\Bergischer HC_Die Eulen Ludwigshafen_16.12.2020_20-21.csv"
path_events = "D:\\Handball\\HBL_Events\\season_21_22\\EventTimelines\\sport_events_23400513_timeline.json"
path_slice = "D:\\Handball\\HBL_Slicing\\season_20_21\\Bergischer HC_Die Eulen Ludwigshafen_16.12.2020_20-21.csv.npy"

positions_path = f"{base_path}HBL_Positions\\{season}\\{match}.csv"
phase_predictions_path = f"{base_path}HBL_Slicing\\{season}\\{match}.csv.npy"
lookup_path = f"{base_path}\\HBL_Events\\lookup\\lookup_matches{season[6:]}.csv"

pitch = pitch.Pitch(xlim=(-20, 20), ylim=(-10, 10), unit="m", boundaries="fixed", sport="handball")

positions = read_position_data_csv(positions_path)
predictions = np.load(phase_predictions_path)
predictions = rolling_mode(predictions, 101)

slices = Code(predictions, "match_phases", {0: "inac", 1: "CATT-A", 2: "CATT-B", 3: "PATT-A", 4: "PATT-B"}, framerate=20)


# get Spielphasen
sequences = slices.find_sequences(return_type="list")
sequences = [x for x in sequences if x[1] - x[0] > slices.framerate]

# Define positions for each phase
phase_positions = {
    0: 2,   # Center (inac)
    1: 3,   # Above center (CATT-A)
    2: 1,  # Below center (CATT-B)
    3: 4,   # Higher above center (PATT-A)
    4: 0   # Lower below center (PATT-B)
}
phase_labels = {
    2: "inac",
    3: "CATT-A",
    1: "CATT-B",
    4: "PATT-A",
    0: "PATT-B"
}

# Initialize lists to hold x (time) and y (position) values for a continuous line
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

# Plot the continuous line without colors
ax.plot(x_vals, y_vals, color="black", linewidth=2)

# Customize the plot
ax.axhline(0, color='grey', linewidth=0.5)  # Centerline
ax.set_yticks(sorted(set(phase_positions.values())))
ax.set_yticklabels([phase_labels[phase] for phase in sorted(phase_positions.keys())])
ax.set_xlabel("Time")
ax.set_title("Continuous Phase Timeline without Color Transitions")
# Set x-axis limit to show only from 0 to 2000
ax.set_xlim(0, 2000)
# Show plot
plt.show()
