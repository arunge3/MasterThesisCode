# from main_structure import approach_plot
# import variables.data_variables as dv
# import pytest
# import os
# import shutil
# import sys
# from pathlib import Path, WindowsPath

# # Add the project root directory to the Python path
# project_root = Path(__file__).parent.parent.parent
# sys.path.append(str(project_root))


# # Get the test data directory path
# TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
# HBL_EVENTS_DIR = TEST_DATA_DIR / "HBL_Events" / "season_20_21" / "Event_Timeline"
# HBL_OUTPUT_DIR = HBL_EVENTS_DIR / "season_20_21"
# HBL_POSITIONS_DIR = TEST_DATA_DIR / "HBL_Positions"
# EXPECTED_RESULTS_DIR = TEST_DATA_DIR / "expected_results"


# @pytest.fixture
# def test_match_id():
#     """Return a test match ID"""
#     return 23400263  # Using one of the match IDs from main.py


# def test_approach_plot_basic(test_match_id):
#     """Test basic functionality of approach_plot with RULE_BASED approach"""
#     # Create approach-specific directories
#     os.makedirs(HBL_OUTPUT_DIR / "Datengrundlagen" /
#                 "rulebased", exist_ok=True)

#     # Copy test data files if they exist
#     if (HBL_EVENTS_DIR / f"{test_match_id}.csv").exists():
#         shutil.copy2(
#             HBL_EVENTS_DIR / f"{test_match_id}.csv",
#             HBL_OUTPUT_DIR / "Datengrundlagen"
#         )

#     if (HBL_POSITIONS_DIR / f"{test_match_id}.csv").exists():
#         shutil.copy2(
#             HBL_POSITIONS_DIR / f"{test_match_id}.csv",
#             HBL_OUTPUT_DIR / "Datengrundlagen"
#         )
