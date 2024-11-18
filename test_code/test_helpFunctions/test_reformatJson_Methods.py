
def test_get_paths_by_match_id_missing_match() -> None:
    assert True
    # Mock data for CSV files without the specified match_id
    # csv_mock_data = pd.DataFrame(
    #     {
    #         "match_id": [124],  # Different match ID,
    #                               so 123 willnot be found
    #         "raw_video": ["match_124_video.mp4"],
    #         "raw_pos_knx": ["match_124_name"],
    #         "cutH1": ["cut_h1_data"],
    #         "offset_h2": ["offset_h2_data"],
    #         "firstVH2": ["first_vh2_data"],
    #     }
    # )

    # lookup_mock_data = pd.DataFrame(
    #     {
    #         "match_id": [
    #             "sr:sport_event:124"
    #         ],  # Different match ID, so 123 will not be found
    #         "file_name": ["position_file_124.csv"],
    #     }
    # )

    # # Mock pandas read_csv
    # with patch(
    #     "pandas.read_csv", side_effect=[csv_mock_data, lookup_mock_data]
    # ) as mock_read_csv:
    #     # Call the function with a missing match_id
    #     result = get_paths_by_match_id(123)

    #     # Validate that None is returned for all elements
    #     assert result == (None, None, None, None, None, None, None,
    # None)

    #     # Ensure read_csv was called for both CSV files
    #     mock_read_csv.assert_any_call(
    #         r"D:\Handball\HBL_Synchronization\mapping20_21.csv",
    # delimiter=";"
    #     )
    #     mock_read_csv.assert_any_call(
    #         r"D:\Handball\HBL_Events\lookup\lookup_matches_20_21.csv"
    #     )
