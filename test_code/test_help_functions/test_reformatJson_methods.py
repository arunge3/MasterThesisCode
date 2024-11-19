
import os
from unittest.mock import patch

import pandas as pd

from help_functions.reformatjson_methods import (get_paths_by_match_id,
                                                 getFirstTimeStampEvent,
                                                 load_first_timestamp_position,
                                                 reformatJson,
                                                 synchronize_time)


class TestreformatJson_Methods:
    base_dir = r"C:\Users\Annabelle\Masterthesis\Code\MasterThesisCode"
    sub_dir_video = r"test_code\test_data\HBL_Videos"
    sub_dir_timeline = r"test_code\test_data\HBL_Events\EventTimeline"
    sub_dir_output = r"test_code\test_data\output"
    sub_dir_position = r"test_code\test_data\HBL_Positions"
    video_base_path = os.path.join(base_dir, sub_dir_video)
    timeline_base_path = os.path.join(base_dir, sub_dir_timeline)
    output_base_path = os.path.join(base_dir, sub_dir_output)
    position_base_path = os.path.join(base_dir, sub_dir_position)

    def test_load_first_timestamp_position(self) -> None:
        filename = "position_file_1234.csv"

        filepath = os.path.join(self.position_base_path, filename)

        date_time, t_null_pos, framerate = load_first_timestamp_position(
            filepath)

        assert date_time == "2020-10-01 16:53:34"
        assert t_null_pos == 1601571214400
        assert framerate == 2

    def test_get_paths_by_match_id(self) -> None:
        # Setup the mock data for the CSV files
        mock_csv_data = pd.DataFrame({
            'match_id': [1234],
            'raw_video': ['video_1234.mp4'],
            'raw_pos_knx': ['match_1234_knx.csv'],
            'cutH1': [32938],
            'offset_h2': [47383],
            'firstVH2': [0]
        })

        mock_lookup_data = pd.DataFrame({
            'match_id': ['sr:sport_event:1234'],
            'file_name': ['position_file_1234.csv']
        })

        # Patch pandas read_csv to return the mock data instead of reading
        # from actual files
        with patch('pandas.read_csv', side_effect=[mock_csv_data,
                                                   mock_lookup_data]):
            # Call the function being tested with a valid match_id
            (video_path, annotation_path, output_path, file_path_position,
             cut_h1, offset_h2, first_vh2,
             match_name) = get_paths_by_match_id(
                1234,
                self.video_base_path,
                self.timeline_base_path,
                self.output_base_path,
                self.position_base_path,
            )

        # Assert the expected paths and data are returned
        assert video_path == os.path.join(
            self.video_base_path, "video_1234.mp4")
        assert annotation_path == os.path.join(
            self.timeline_base_path,
            "sport_events_1234_timeline.json")
        assert output_path == os.path.join(
            self.output_base_path,
            "sport_events_1234_timeline_reformatted.jsonl")
        assert file_path_position == os.path.join(
            self.position_base_path, "position_file_1234.csv")
        assert cut_h1 == 32938
        assert offset_h2 == 47383
        assert first_vh2 == 0
        assert match_name == "match_1234_knx.csv"

    def test_synchronize_time(self) -> None:
        event_time_str = "2020-10-01T17:00:11+00:00"
        second_half = False
        first_timestamp_opt = ("2020-10-01 16:53:34", 1601571214400, 20)
        offset_fr = 44638
        offseth2_fr = 0
        first_vh2 = 0
        fps = 29.97
        result = synchronize_time(event_time_str, second_half,
                                  first_timestamp_opt, offset_fr,
                                  offseth2_fr, first_vh2, fps)
        assert result == 56536.09

    def test_getFirstTimeStampEvent(self) -> None:
        filename = "sport_events_1234_timeline.json"
        filepath = os.path.join(self.timeline_base_path, filename)
        result = getFirstTimeStampEvent(filepath)
        assert result == '2020-10-01T17:00:11+00:00'

    def test_reformatJson(self) -> None:
        filename = "sport_events_1234_timeline.json"
        path_timeline_full = os.path.join(self.timeline_base_path, filename)
        filename = "sport_events_1234_timeline_reformatted.jsonl"
        path_output_full = os.path.join(self.output_base_path, filename)
        first_timestamp_opt = ("2020-10-01 16:53:34", 1601571214400, 20)
        path_expected_output = os.path.join(self.output_base_path,
                                            "expected_output.jsonl")
        offset_fr = 44638
        offseth2_fr = 0
        first_vh2 = 0
        fps = 29.97
        result = reformatJson(path_timeline_full, path_output_full,
                              first_timestamp_opt, offset_fr, offseth2_fr,
                              first_vh2, fps)
        assert (result is None)
        with (open(path_output_full, 'r') as file1,
              open(path_expected_output, 'r') as file2):
            for line1, line2 in zip(file1, file2):
                assert line1 == line2
