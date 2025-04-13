"""
This module implements core template matching functionality
for handball match analysis. It provides functions for scaling
coordinates and matching player positions against predefined
formation templates to identify team formations during the game.

Author:
    @Annabelle Runge

Date:
    2025-04-01
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist


def scale_coords_from_zero_to_one(coords: np.ndarray,
                                  aspect_x: int = 1,
                                  aspect_y: float = 0.5
                                  ) -> np.ndarray:
    """
    scales coordinates in numpy array from zero to specific
    aspect ratio, e.g. x{0, 1} and y{0, 0.5) for handball pitch.
    Parameters
    ----------
    coords: np.array of shape (t, 2*n), organized like xy-object


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


def template_matching(coords: np.ndarray,
                      templates: dict[str, list[np.ndarray]]
                      ) -> dict[str, float]:
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
    # Templates normalisieren
    for key in templates:
        templates[key] = scale_coords_from_zero_to_one(
            np.array(templates[key]).flatten().reshape(-1, 2)
        )

    # Durchschnittliche Position und Rollenverteilung berechnen
    avg_pos = np.nanmean(coords.xy, axis=0)
    nan_cols = np.argwhere(np.isnan(coords).all(axis=0)).reshape(-1)
    coords_clean = np.delete(coords, nan_cols, 1)
    avg_pos = np.delete(avg_pos, nan_cols, 0)

    # Positionen für jedes Frame lösen
    solved_pos = np.full(
        (coords_clean.shape[0], int(coords_clean.shape[1]/2), 2), np.NaN)
    for i, frame in enumerate(coords_clean):
        cost_mat = cdist(frame.reshape((-1, 2)), avg_pos.reshape((-1, 2)))
        cost_mat = np.where(np.isnan(cost_mat), 1000000, cost_mat)
        row, col = linear_sum_assignment(cost_mat)

        solved_frame = np.full((int(coords_clean.shape[1]/2), 2), np.NaN)
        solved_frame[row] = frame.reshape((-1, 2))[col]
        solved_pos[i] = solved_frame

    # Finale Ähnlichkeitsberechnung
    avg_pos_scaled = scale_coords_from_zero_to_one(
        np.nanmean(solved_pos, axis=0))
    return {
        formation: 1 - np.square(cdist(avg_pos_scaled, templates[formation]))[
            linear_sum_assignment(
                np.square(cdist(avg_pos_scaled, templates[formation])))
        ].mean() * 3
        for formation in templates
    }
