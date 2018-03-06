import numpy as np


class IrregularPresamplesArray:
    """A wrapper around a list of memory-mapped Numpy arrays with heterogeneous shapes.

    This class provides a simple way to consistently sample arrays with different shapes and datatypes.

    Input arguments:

    * ``filepaths``: An iterable of (Numpy array filepath, shape as tuple).

    """
    def __init__(self, filepaths):
        self.count = 0
        self.data = [
            (np.load(str(fp), mmap_mode='r'), shape[1])
            for fp, shape in filepaths
        ]

    def sample(self, index):
        """Draw a new sample from the pre-sampled arrays"""
        result = np.hstack([arr[:, index % ncols] for arr, ncols in self.data])
        self.count += 1
        return result
