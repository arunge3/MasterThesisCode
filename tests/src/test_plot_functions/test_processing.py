# import json
# import os
# from typing import Any
# from unittest import TestCase
# from unittest.mock import patch

# from plot_functions.processing import (add_threshold_to_time, adjust_timestamp,
#                                        calculate_correct_phase,
#                                        calculate_inactive_phase,
#                                        calculate_sequences, calculate_timeouts,
#                                        calculate_timeouts_over,
#                                        check_same_phase, give_last_event,
#                                        search_phase, synchronize_events)


# class TestProcessing(TestCase):
#     base_dir_temp = (r"C:\Users\Annabelle\Masterthesis\Code\MasterThesisCode")
#     base_dir = os.path.join(base_dir_temp, r"test_code\test_data")
#     base_dir_str = (
#         "C:\\Users\\Annabelle\\Masterthesis\\Code\\MasterThesisCode")
#     base_dir_str = base_dir_str + "\\test_code\\test_data\\"
#     sub_dir_video = (r"HBL_Videos")
#     sub_dir_timeline = (
#         r"HBL_Events\EventTimeline\sport_events_1234_timeline.json")
#     sub_dir_output = (r"output")
#     sub_dir_position = (
#         r"HBL_Positions\position_file_1234.csv")
#     video_base_path = os.path.join(base_dir, sub_dir_video)
#     timeline_base_path = os.path.join(base_dir, sub_dir_timeline)
#     output_base_path = os.path.join(base_dir, sub_dir_output)
#     position_base_path = os.path.join(base_dir, sub_dir_position)
#     expected_path = os.path.join(
#         base_dir, r"expected_results")
#     csv_file = os.path.join(
#         base_dir, r"HBL_Synchronization\mapping20_21.csv")
#     lookup_file = os.path.join(
#         base_dir, r"HBL_Events\lookup\lookup_matches_20_21.csv")

#     team_info = {'Heimteam': 'home', 'Auswaerts Team': 'away'}
#     sequences = [(0, 7942, 0), (7942, 8664, 4), (8664, 8735, 1),
#                  (8735, 8877, 0), (8877, 9356, 3), (9356, 9430, 0),
#                  (9430, 9525, 4), (9525, 9703, 0), (9703, 9827, 3),
#                  (9827, 10008, 0), (10008, 10384, 3), (10384, 10511, 0),
#                  (10511, 10980, 3), (10980, 11079, 2), (11079, 11232, 0),
#                  (11232, 11671, 3), (11671, 11868, 0), (11868, 11930, 3),
#                  (11930, 12808, 0), (12808, 12917, 3), (12917, 13000, 0),
#                  (13000, 15000, 1), (15000, 220100, 0), (220100, 230536, 1),
#                  (230536, 230690, 0)]
#     event_only = {
#         'id': 756467251,
#         'type': 'score_change',
#         'time': 106106,
#         'match_time': 21,
#         'match_clock': '20:31',
#         'competitor': 'home',
#         'home_score': 11,
#         'away_score': 9,
#         'scorer': {
#                 'id': 'sr:player:125146',
#                 'name': 'Pevnov, Evgeni'
#         },
#         'assists': [{'id': 'sr:player:905894',
#                      'name': 'Jonsson, Alfred', 'type': 'primary'}],
#         'zone': 'six_meter_centre',
#         'players': [{'id': 'sr:player:125160',
#                      'name': 'Semisch, Malte', 'type': 'goalkeeper'}],
#         'shot_type': 'pivot'
#     }

#     @patch('help_functions.reformatjson_methods.get_paths_by_match_id',
#            autospec=True)
#     def test_adjust_timestamp(self: Any, mock_get_paths: Any) -> None:
#         # Mock-Value definition
#         expected_value = (self.video_base_path, self.timeline_base_path,
#                           self.output_base_path, self.position_base_path,
#                           9345, 0, 0, "")

#         mock_get_paths.return_value = expected_value
#         # Call the method under test
#         match_id = 1234
#         events, team_info = adjust_timestamp(match_id)

#         # Assertions
#         mock_get_paths.assert_called_once_with(match_id)
#         self.assertEqual(len(events), 35)
#         self.assertIn("Heimteam", team_info)
#         self.assertIn("Auswaerts Team", team_info)

#         # Verify adjusted timestamps (just an example)
#         self.assertEqual(events[0]["time"], 792)
#         self.assertEqual(events[21]["time"], 4100)

#     @patch('help_functions.reformatjson_methods.get_paths_by_match_id',
#            autospec=True)
#     def test_calculate_sequences(self: Any, mock_get_paths: Any) -> None:
#         expected_value = (self.video_base_path, self.timeline_base_path,
#                           self.output_base_path, self.position_base_path,
#                           9345, 0, 0,
#                           r"Heimteam_Auswaert Team_01.10.2020_20-21.csv")

#         mock_get_paths.return_value = expected_value

#         results = calculate_sequences(1234, self.base_dir_str)
#         assert results[:20] == self.sequences[:20]

#     def test_synchronize_events(self: Any) -> None:

#         path_expected_output = os.path.join(self.expected_path,
#                                             "expected_output_time_only.json")
#         path_expected_synchronize_events = os.path.join(
#             self.expected_path, "expected_events_synchronize.json")

#         with open(path_expected_output, 'r') as file:
#             event_json = json.load(file)
#         events = event_json.get("timeline", [])
#         results = synchronize_events(events, self.sequences, self.team_info)

#         with open(path_expected_synchronize_events, "r",
#                   encoding="utf-8") as file:
#             loaded_variables = json.load(file)

#         loaded_variables = (
#             loaded_variables[0],
#             [tuple(item) for item in loaded_variables[1]]
#         )
#         assert results == loaded_variables

#     def test_searchPhase(self: Any) -> None:
#         results = search_phase(13865, self.sequences, "A")
#         assert results == 12916
#         results = search_phase(13865, self.sequences, "B")
#         assert results == 11078

#     def test_give_last_event(self: Any) -> None:
#         path_expected_output = os.path.join(self.expected_path,
#                                             "expected_output_time_only.json")

#         with open(path_expected_output, 'r') as file:
#             event_json = json.load(file)
#         last_event = {
#             'id': 756467251,
#             'type': 'score_change',
#             'time': 106106,
#             'match_time': 21,
#             'match_clock': '20:31',
#             'competitor': 'home',
#             'home_score': 11,
#             'away_score': 9,
#             'scorer': {
#                     'id': 'sr:player:125146',
#                     'name': 'Pevnov, Evgeni'
#             },
#             'assists': [{'id': 'sr:player:905894',
#                         'name': 'Jonsson, Alfred', 'type': 'primary'}],
#             'zone': 'six_meter_centre',
#             'players': [{'id': 'sr:player:125160',
#                         'name': 'Semisch, Malte', 'type': 'goalkeeper'}],
#             'shot_type': 'pivot'
#         }
#         events = event_json.get("timeline", [])
#         result = give_last_event(events, 106346)
#         assert result == last_event

#     def test_add_threshold_to_time(self: Any) -> None:
#         result = add_threshold_to_time(self.event_only)
#         assert result == 105997.24

#     def test_calculate_inactive_phase(self: Any) -> None:
#         result = calculate_inactive_phase(8860, sequences=self.sequences)
#         assert result == 8860
#         result = calculate_inactive_phase(9520, sequences=self.sequences)
#         assert result == 9429

#     def test_calculate_timeouts(self: Any) -> None:
#         timeout = {
#             "id": 756505775,
#             "type": "timeout",
#             "time": "2020-10-01T18:25:30+00:00",
#             "match_time": 54,
#             "match_clock": "53:23",
#             "competitor": "away"
#         }
#         result = calculate_timeouts(209952, self.sequences, "A", timeout)
#         assert result == 209952

#     def test_calculate_timeouts_over(self: Any) -> None:
#         path_expected_output = os.path.join(self.expected_path,
#                                             "expected_output_time_only.json")

#         with open(path_expected_output, 'r') as file:
#             event_json = json.load(file)
#         events = event_json.get("timeline", [])
#         event = {
#             "id": 756506263,
#             "type": "timeout_over",
#             "time": 211570,
#             "match_time": 54,
#             "match_clock": "53:23"
#         }
#         result = calculate_timeouts_over(self.sequences, event, events)
#         assert result == 211570

#     def test_checkSamePhase(self: Any) -> None:
#         result = check_same_phase(209952, 211570, self.sequences, 0)
#         assert 211570 == result
#         with self.assertRaises(ValueError):
#             result = check_same_phase(209952, 230234, self.sequences, 1)

#     def test_calculate_correct_phase(self: Any) -> None:
#         event_new = self.event_only
#         result = calculate_correct_phase(
#             106106, self.sequences, "A", event_new)
#         assert result["time"] == 14999
#         assert result["type"] == self.event_only["type"]
#         result = calculate_correct_phase(
#             106106, self.sequences, "B", event_new)
#         assert result["time"] == 11078
#         assert result["type"] == self.event_only["type"]
#         event_new["time"] = 7950
#         result = calculate_correct_phase(
#             7950, self.sequences, "B", event_new)
#         assert result["time"] == 7950
#         assert result["type"] == event_new["type"]
#         event_new['time'] = 8670
#         result = calculate_correct_phase(
#             8670, self.sequences, "A", event_new)
#         assert result["time"] == 8670
#         assert result["type"] == event_new["type"]
