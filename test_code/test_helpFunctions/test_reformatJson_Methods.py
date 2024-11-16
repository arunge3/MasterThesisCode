import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.helpFunctions import reformatJson_Methods


def test_get_paths_by_match_id(mock_join, mock_read_csv):
    # Mock data for CSV files
    mock_csv_data = pd.DataFrame({
        "match_id": [1],
        "raw_video": ["video.mp4"],
        "raw_pos_knx": ["Match_01"],
        "cutH1": ["10:00"],
        "offset_h2": ["20:00"],
        "firstVH2": ["video_h2.mp4"],
    })

    mock_lookup_data = pd.DataFrame({
        "match_id": ["sr:sport_event:1"],
        "file_name": ["position_file.csv"]
    })

    # Mock the return values of read_csv
    mock_read_csv.side_effect = [mock_csv_data, mock_lookup_data]

    # Mock os.path.join behavior
    mock_join.side_effect = lambda *args: "/".join(args)

    # Call the function with a mock match_id
    result = reformatJson_Methods.get_paths_by_match_id(1)

    # Assert the expected results
    assert result == (
        "/D:/Handball/HBL_Videos/season_2021/video.mp4",
        "/D:/Handball/HBL_Events/season_20_21/EventTimeline/sport_events_1_timeline.json",
        "/D:/Handball/HBL_Events/season_20_21/EventJson/sport_events_1_timeline_reformatted.jsonl",
        "/D:/Handball/HBL_Positions/20-21/position_file.csv",
        "10:00",
        "20:00",
        "video_h2.mp4",
        "Match_01",
    )

    # Assert the read_csv calls
    mock_read_csv.assert_any_call("D:/Handball/HBL_Synchronization/mapping20_21.csv", delimiter=";")
    mock_read_csv.assert_any_call("D:/Handball/HBL_Events/lookup/lookup_matches_20_21.csv")

    # Assert os.path.join calls
    mock_join.assert_any_call("D:/Handball/HBL_Videos/season_2021", "video.mp4")
    mock_join.assert_any_call("D:/Handball/HBL_Positions/20-21", "position_file.csv")
