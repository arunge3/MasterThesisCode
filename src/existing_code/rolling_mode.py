from scipy.stats import mode
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _mode(signal):
    """signal: data array of shape (signal length x window length), mode is
    calculated for each row
    returns: modes of each row (window), results in shape (signal length x 1)"""
    return mode(signal, axis=1)[0]


def rolling_mode(signal: np.array, window_size: int):
    """smoothes with rolling mode, window starts at i and only looks into the future
    (could be changed)
    signal: array-like, categorical 1-D signal (predictions)
    window_size: in frames, needs to be odd
    """
    rolled_signal = signal.copy()
    windows = sliding_window_view(signal, window_shape=window_size)
    modes = _mode(windows)
    rolled_signal[int(window_size/2) : - int(window_size/2)] = modes.squeeze()

    return rolled_signal