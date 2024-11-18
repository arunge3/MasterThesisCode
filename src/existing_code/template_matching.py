import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist


def scale_coords_from_zero_to_one(coords, aspect_x=1, aspect_y=0.5):
    """
    scales coordinates in numpy array from zero to specific aspect ratio, e.g.
    x{0, 1} and y{0, 0.5) for handball pitch.
    Parameters
    ----------
    coords
    np.array of shape (t, 2*n), organized like xy-object

    Returns
    -------
    scaled_xy: np.array with rescaled coords
    """
    min_x, max_x = np.nanmin(coords[:, ::2]), np.nanmax(coords[:, ::2])
    min_y, max_y = np.nanmin(coords[:, 1::2]), np.nanmax(coords[:, 1::2])

    scaled_x = (coords[:, ::2] - min_x) / (max_x - min_x) * aspect_x
    scaled_y = (coords[:, 1::2] - min_y) / (max_y - min_y) * aspect_y

    scaled_xy = np.dstack([scaled_x, scaled_y]).flatten().reshape(coords.shape)

    return scaled_xy


def template_matching(coords, templates):
    """
    Performs formation recognition with template matching. Note that the
    coordinates and the stemplates have to be in the same playing
    direction, e.g. from left to right so the template matching makes sense
    Parameters
    ----------
    coords: xy object the template matching should be performed on
    templates: dict with keys: names of the templates, values: lists
    of coordinates, like in xy.object

    Returns
    -------
    fsim: dict with keys: template names and value: respective fsim value
    """

    # normalize templates from 0 to 1
    for key in templates:
        templates[key] = np.array(templates[key]).reshape((1, 12))
        # plt.scatter(templates[key][:, ::2], templates[key][:, 1::2])
        templates[key] = scale_coords_from_zero_to_one(templates[key])
        # plt.scatter(templates[key][:, ::2], templates[key][:, 1::2])

    # initial role assignment
    average_position = np.nanmean(coords.xy, axis=0)

    # solve for role swaps
    # find and delete columns with nan because
    # linear_sum_assignment()
    # function is a pussy
    nan_cols = np.argwhere(np.isnan(coords).all(axis=0)).reshape(-1)
    coords_nonan = np.delete(coords, nan_cols, 1)
    average_position = np.delete(average_position, nan_cols, 0)
    solved_pos = np.full(
        (coords_nonan.shape[0], int(coords_nonan.shape[1] / 2), 2), np.NaN
    )

    # loop through frames and assign role for each frame
    for i, frame in enumerate(coords_nonan):
        # remove nans from frame
        frame_nan = np.argwhere(np.isnan(frame)).reshape(-1)
        frame_nonan = np.delete(frame, frame_nan)
        # calculate cost_matrix between frame and initial role
        cost_matrix = cdist(frame.reshape((-1, 2)),
                            average_position.reshape((-1, 2)))
        # set nans in cost matrix to high values so they are
        # disregarded (hopefully)
        cost_matrix = np.where(np.isnan(cost_matrix) ==
                               True, 1000000, cost_matrix)
        # solve linear sum assignment
        row, col = linear_sum_assignment(cost_matrix)
        # sort coordinates into solved roles
        solved_frame = np.full((int(coords_nonan.shape[1] / 2), 2), np.NaN)
        solved_frame[row] = frame.reshape((-1, 2))[col]
        solved_pos[i] = solved_frame

    average_position_solved = np.nanmean(solved_pos, axis=0)

    # normalize coords from 0 to 1
    average_position_scaled = scale_coords_from_zero_to_one(
        average_position_solved)

    fsims = {}
    for formation in templates:
        cost_matrix = np.square(
            cdist(
                average_position_scaled,
                templates[formation].reshape(
                    int(templates[formation].shape[1] / 2), 2),
            )
        )
        row, col = linear_sum_assignment(cost_matrix)
        cost = cost_matrix[row, col].mean()
        fsim = 1 - cost * 3
        fsims.update({formation: fsim})

    return fsims
