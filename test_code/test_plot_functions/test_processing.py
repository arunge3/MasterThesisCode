import os
from typing import Any
from unittest import TestCase
from unittest.mock import patch

from plot_functions.processing import adjustTimestamp


class TestProcessing(TestCase):
    base_dir_temp = (r"C:\Users\Annabelle\Masterthesis\Code\MasterThesisCode")
    base_dir_temp2 = r"test_code\test_data"
    base_dir = os.path.join(base_dir_temp, base_dir_temp2)
    sub_dir_video = (r"HBL_Videos")
    sub_dir_timeline = (
        r"HBL_Events\EventTimeline\sport_events_1234_timeline.json")
    sub_dir_output = (r"output")
    sub_dir_position = (
        r"HBL_Positions\position_file_1234.csv")
    video_base_path = os.path.join(base_dir, sub_dir_video)
    timeline_base_path = os.path.join(base_dir, sub_dir_timeline)
    output_base_path = os.path.join(base_dir, sub_dir_output)
    position_base_path = os.path.join(base_dir, sub_dir_position)
    expected_path = os.path.join(
        base_dir, r"expected_results")
    csv_file = os.path.join(
        base_dir, r"HBL_Synchronization\mapping20_21.csv")
    lookup_file = os.path.join(
        base_dir, r"HBL_Events\lookup\lookup_matches_20_21.csv")

    @patch('help_functions.reformatjson_methods.get_paths_by_match_id',
           autospec=True)
    def test_adjust_timestamp(self: Any, mock_get_paths: Any) -> None:
        # Mock-Wert definieren
        expected_value = (self.video_base_path, self.timeline_base_path,
                          self.output_base_path, self.position_base_path,
                          9345, 0, 0, "")

        # Mock konfigurieren
        mock_get_paths.return_value = expected_value
        # Call the method under test
        match_id = 1234
        events, team_info = adjustTimestamp(match_id)

        # Assertions
        mock_get_paths.assert_called_once_with(match_id)
        self.assertEqual(len(events), 33)
        self.assertIn("Heimteam", team_info)
        self.assertIn("Auswaerts Team", team_info)

        # Verify adjusted timestamps (just an example)
        self.assertEqual(events[0]["time"], 792)
        self.assertEqual(events[21]["time"], 4094)


def test_adjustTimestamp() -> None:
    # match_id = 12345
    # result = adjustTimestamp(match_id)
    assert True  # Adjust this assertion based on the actual expected result


def test_calculate_sequences() -> None:
    assert True


def test_synchronize_events() -> None:
    assert True


def test_searchPhase() -> None:
    assert True


def test_give_last_event() -> None:
    assert True


def test_add_threshold_to_time() -> None:
    assert True


def test_calculate_inactive_phase() -> None:
    assert True


def test_calculate_timeouts() -> None:
    assert True


def test_calculate_timeouts_over() -> None:
    assert True


def test_checkSamePhase() -> None:
    assert True


def test_calculate_correct_phase() -> None:
    assert True
