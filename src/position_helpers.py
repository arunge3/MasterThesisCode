from typing import Any

import numpy as np
from floodlight import XY
from floodlight.models.kinematics import AccelerationModel


def prepare_ball_data(ball_data: Any) -> tuple[Any, Any]:
    """
    Prepares the ball data for the cost function.
    Args:
        ball_data: The ball data

    Returns:
        tuple: The ball data and the acceleration of the ball
    """
    if ball_data.N == 1:
        ball_positions = ball_data.player(0)
    else:
        ball_data_1 = ball_data.player(0)
        ball_data_2 = ball_data.player(1)

        ball_positions = combine_ball_data(ball_data_1, ball_data_2)

        if ball_data.N > 2:

            # Process any additional ball data players if they exist
            for i in range(3, ball_data.N+1):
                ball_data_i = ball_data.player(i)
                ball_positions = combine_ball_data(ball_positions, ball_data_i)
                # Here you could add logic to combine additional ball data
    combined_ball_data = XY(ball_positions.reshape(-1, 2),
                            framerate=ball_data.framerate)

    ball_acceleration = get_acceleration_cost(combined_ball_data)

    return ball_positions, ball_acceleration


def combine_ball_data(ball_data_1: Any, ball_data_2: Any) -> Any:
    """
    Combines the ball data for the cost function.
    Args:
        ball_data_1: The first ball data
        ball_data_2: The second ball data

    Returns:
        The combined ball data
    """
    if ball_data_1.shape != ball_data_2.shape:
        if ball_data_1.size == 0:
            ball_positions = ball_data_2
        elif ball_data_2.size == 0:
            ball_positions = ball_data_1
        else:

            raise ValueError(
                f"Ball data arrays have different shapes: "
                f"{ball_data_1.shape} and {ball_data_2.shape}")

    else:
        both_valid = ~np.isnan(ball_data_1) & ~np.isnan(ball_data_2)
        if np.any(both_valid):
            ball_positions = combine_both_valid_ball_data(
                ball_data_1, ball_data_2)

            first_idx = np.where(both_valid)[0][0] if np.any(
                both_valid) else 'N/A'
            print(f"Warning: Found {np.sum(both_valid)}"
                  f" positions where both ball tracks have valid data. "
                  f"First occurrence at index {first_idx}")
        else:
            ball_positions = np.where(
                ~np.isnan(ball_data_1), ball_data_1,
                np.where(~np.isnan(ball_data_2), ball_data_2, np.nan))

    return ball_positions


def combine_both_valid_ball_data(ball_data_1: Any,
                                 ball_data_2: Any) -> Any:
    """
    Combines two ball data sets by selecting the active ball at each time step.
    Args:
        ball_data_1: The first ball data set
        ball_data_2: The second ball data set

    Returns:
        The combined ball data
    """
    if not isinstance(ball_data_1, XY):
        ball_data_1 = XY(ball_data_1.reshape(-1, 2),
                         framerate=20)
    if not isinstance(ball_data_2, XY):
        ball_data_2 = XY(ball_data_2.reshape(-1, 2),
                         framerate=20)
    # ball_acceleration_1 = get_acceleration_cost(ball_data_1)
    # ball_acceleration_2 = get_acceleration_cost(ball_data_2)

    ball_positions = np.empty_like(ball_data_1)

    for i in range(len(ball_data_1)):
        if np.isnan(ball_data_1[i]).any():
            ball_positions[i] = ball_data_2[i]
        elif np.isnan(ball_data_2[i]).any():
            ball_positions[i] = ball_data_1[i]
        else:
            # Both balls have valid data at this position
            # Look for continuous segments where both balls have valid data
            start_i = i
            end_i = i
            while (end_i < len(ball_data_1)
                   and not np.isnan(ball_data_1[end_i]).any()
                   and not np.isnan(ball_data_2[end_i]).any()):
                end_i += 1

            # Calculate the total distance traveled by
            # each ball between start_i and end_i
            ball_1_positions = ball_data_1[start_i:end_i]
            ball_2_positions = ball_data_2[start_i:end_i]

            # Calculate distances between consecutive points
            ball_1_diffs = np.diff(ball_1_positions, axis=0)
            ball_2_diffs = np.diff(ball_2_positions, axis=0)

            # Calculate Euclidean distances
            ball_1_distances = np.sqrt(np.sum(ball_1_diffs**2, axis=1))
            ball_2_distances = np.sqrt(np.sum(ball_2_diffs**2, axis=1))

            # distance-based selection
            ball_1_total_distance = np.sum(ball_1_distances)
            ball_2_total_distance = np.sum(ball_2_distances)

            if ball_1_total_distance < ball_2_total_distance:
                ball_positions[start_i:end_i] = ball_data_1[start_i:end_i]
            else:
                ball_positions[start_i:end_i] = ball_data_2[start_i:end_i]

            # Skip to the end of the processed segment
            i = end_i - 1
    return ball_positions


def get_acceleration_cost(pos_data: Any) -> Any:
    """
    Calculates the acceleration cost for the ball.
    Args:
        pos_data: The position data

    Returns:
        The acceleration cost
    """
    am = AccelerationModel()
    am.fit(pos_data)

    ball_acceleration = am.acceleration()
    if ball_acceleration is None:
        raise ValueError("AccelerationModel.acceleration() returned None. "
                         "Check if fit() was successful.")

    ball_acceleration = np.hstack(ball_acceleration)
    return ball_acceleration
