
import os
from unittest.mock import patch

import pandas as pd

from helpFunctions.reformatJson_methods import get_paths_by_match_id


def test_get_paths_by_match_id() -> None:
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
        'file_name': ['position_file_1234.txt']
    })

    # Patch pandas read_csv to return the mock data instead of reading
    # from actual files
    with patch('pandas.read_csv', side_effect=[mock_csv_data,
                                               mock_lookup_data]):
        # Call the function being tested with a valid match_id
        (video_path, annotation_path, output_path, file_path_position, cut_h1,
         offset_h2, first_vh2, match_name) = get_paths_by_match_id(
            1234,
            video_base_path="path/to/videos",
            annotation_base_path="path/to/annotations",
            output_base_path="path/to/output",
            position_base_path="path/to/positions"
        )

    # Assert the expected paths and data are returned
    assert video_path == os.path.join("path/to/videos", "video_1234.mp4")
    assert annotation_path == os.path.join(
        "path/to/annotations", "sport_events_1234_timeline.json")
    assert output_path == os.path.join(
        "path/to/output", "sport_events_1234_timeline_reformatted.jsonl")
    assert file_path_position == os.path.join(
        "path/to/positions", "position_file_1234.txt")
    assert cut_h1 == 32938
    assert offset_h2 == 47383
    assert first_vh2 == 0
    assert match_name == "match_1234_knx.csv"
