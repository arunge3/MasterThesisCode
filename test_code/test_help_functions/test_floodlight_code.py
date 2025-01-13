from unittest.mock import MagicMock, patch

import matplotlib
import pytest
from matplotlib import pyplot as plt

from help_functions.floodlight_code import Approach, plot_phases

matplotlib.use("Agg")  # Use a non-interactive backend


@patch("help_functions.floodlight_code.plt.show")
@patch("help_functions.floodlight_code.processing.calculate_sequences")
@patch("help_functions.floodlight_code.calculate_event_stream")
@patch("help_functions.floodlight_code.synchronize_events_fl")
@patch("help_functions.floodlight_code.berechne_phase_und_speichern_fl")
def test_plot_phases_rule_based(
    mock_berechne_phase: MagicMock,
    mock_sync_events: MagicMock,
    mock_calc_event_stream: MagicMock,
    mock_calc_sequences: MagicMock,
    mock_plt_show: MagicMock,
) -> None:

    # Mock the return values of the patched functions
    mock_calc_sequences.return_value = [(0, 1000, 1), (1000, 2000, 2)]
    mock_calc_event_stream.return_value = ([], 0, [])
    mock_sync_events.return_value = ([], [(0, 1000, 1), (1000, 2000, 2)])

    # Call the function with a sample match_id and Approach.RULE_BASED
    plot_phases(23400263, Approach.RULE_BASED)

    # Assert that the mocked functions were called with expected arguments
    mock_calc_sequences.assert_called_once_with(23400263)
    mock_calc_event_stream.assert_called_once_with(23400263)
    mock_sync_events.assert_called_once()
    mock_berechne_phase.assert_called_once()
    mock_plt_show.assert_called_once()

    # Ensure plots are closed after the test
    plt.close("all")  # Close all open plots


@patch("help_functions.floodlight_code.processing.calculate_sequences")
@patch("help_functions.floodlight_code.processing.adjust_timestamp_baseline")
@patch("help_functions.floodlight_code.berechne_phase_und_speichern_fl")
def test_plot_phases_baseline(mock_berechne_phase: MagicMock,
                              mock_adjust_timestamp: MagicMock,
                              mock_calc_sequences: MagicMock
                              ) -> None:
    # Mock the return values of the patched functions
    mock_calc_sequences.return_value = [(0, 1000, 1), (1000, 2000, 2)]
    mock_adjust_timestamp.return_value = ([], [])

    # Call the function with a sample match_id and Approach.BASELINE
    plot_phases(23400263, Approach.BASELINE)

    # Assert that the mocked functions were called with expected arguments
    mock_calc_sequences.assert_called_once_with(23400263)
    mock_adjust_timestamp.assert_called_once_with(23400263)
    mock_berechne_phase.assert_called_once()
    # Ensure plots are closed after the test
    plt.close("all")  # Close all open plots


def test_plot_phases_invalid_approach() -> None:
    # Test with an invalid approach
    with pytest.raises(ValueError, match="Invalid approach specified!"):
        plot_phases(23400263, "INVALID_APPROACH")
        plt.close("all")  # Close all open plots
