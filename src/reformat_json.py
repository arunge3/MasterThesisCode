import help_functions.reformatJson_methods as helpFuctions

"""
This module reformats JSON data for handball match videos, providing
functionality to process and transform match data into a standardized
format.

Author:
    @Annabelle Runge

Date:
    2025-04-01

Modules:
    helpFunctions.reformatJson_Methods: Contains helper functions
    for reformatting JSON data.

Constants:
    fps (float): Frames per second of the video.
    match_id (int): Unique identifier for the match.

Functions:
    helpFuctions.get_paths_by_match_id(match_id):
        Retrieves various file paths based on the match ID.
        Args:
            match_id (int): Unique identifier for the match.
        Returns:
            tuple: Contains paths for video, timeline, output JSONL,
            position file, cut height, offset, and first video height.
    helpFuctions.load_first_timestamp_and_offset(file_path_position):
        Loads the first timestamp and offset from the position file.
    helpFuctions.reformatJson(path_timeline, path_output_jsonl,
    first_timestamp_ms, cut_h1, offset_h2, first_vh2, fps):
        Reformats the JSON data based on the provided parameters.
        Args:
            path_timeline (str): Path to the timeline file.
            path_output_jsonl (str): Path to the output JSONL file.
            first_timestamp_ms (int): First timestamp in milliseconds.
            cut_h1 (int): Cut height parameter.
            offset_h2 (int): Offset parameter.
            first_vh2 (int): First video height parameter.
            fps (float): Frames per second of the video.
"""

# Main script
fps = 29.97  # Frames pro Sekunde
match_id = 23400263
(
    video_path,
    path_timeline,
    path_output_jsonl,
    file_path_position,
    cut_h1,
    offset_h2,
    first_vh2,
    _,
) = helpFuctions.get_paths_by_match_id(match_id)

first_timestamp_ms = helpFuctions.load_first_timestamp_position(
    file_path_position)
helpFuctions.reformat_json(
    path_timeline,
    path_output_jsonl,
    first_timestamp_ms,
    cut_h1,
    offset_h2,
    first_vh2,
    fps,
)
