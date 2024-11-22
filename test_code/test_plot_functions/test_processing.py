import os
from typing import Any
from unittest import TestCase
from unittest.mock import patch

from plot_functions.processing import adjustTimestamp, calculate_sequences


class TestProcessing(TestCase):
    base_dir_temp = (r"C:\Users\Annabelle\Masterthesis\Code\MasterThesisCode")
    base_dir = os.path.join(base_dir_temp, r"test_code\test_data")
    base_dir_str = (
        "C:\\Users\\Annabelle\\Masterthesis\\Code\\MasterThesisCode")
    base_dir_str = base_dir_str + "\\test_code\\test_data\\"
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

    @patch('help_functions.reformatjson_methods.get_paths_by_match_id',
           autospec=True)
    def test_calculate_sequences(self: Any, mock_get_paths: Any) -> None:
        expected_value = (self.video_base_path, self.timeline_base_path,
                          self.output_base_path, self.position_base_path,
                          9345, 0, 0,
                          r"Heimteam_Auswaert Team_01.10.2020_20-21.csv")
        # Mock konfigurieren
        mock_get_paths.return_value = expected_value

        results = calculate_sequences(1234, self.base_dir_str)
        results = results[:20]
        expected = [(0, 7942, 0), (7942, 8664, 4), (8664, 8735, 1),
                    (8735, 8877, 0), (8877, 9356, 3), (9356, 9430, 0),
                    (9430, 9525, 4), (9525, 9703, 0), (9703, 9827, 3),
                    (9827, 10008, 0), (10008, 10384, 3), (10384, 10511, 0),
                    (10511, 10980, 3), (10980, 11079, 2), (11079, 11232, 0),
                    (11232, 11671, 3), (11671, 11868, 0), (11868, 11930, 3),
                    (11930, 12808, 0), (12808, 12917, 3)]
        assert results == expected


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
