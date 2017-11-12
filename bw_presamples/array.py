from numpy.random import RandomState
import numpy as np


class IrregularPresamplesArray(RandomState):
    """A wrapper around a list of memory-mapped Numpy arrays with heterogeneous shapes.

    This class provides a simple way to consistently sample arrays with different shapes and datatypes.

    Input arguments:

    * ``filepaths``: An iterable of (Numpy array filepath, shape as tuple).
    * ``seed``: Seed for RNG. Optional.

    """
    def __init__(self, filepaths, seed=None):
        super(IrregularPresamplesArray, self).__init__(seed)
        self.seed_value = seed

        self.data = [
            (np.load(fp, mmap_mode='r'), shape[1])
            for fp, shape in filepaths
        ]

    def sample(self):
        """Draw a new sample from the pre-sample arrays"""
        # Max signed 32 bit integer, compatible with Windows
        index = self.randint(0, 2147483647)
        arr = np.hstack([arr[:, index % ncols] for arr, ncols in self.data])
        return np.hstack([arr[:, index % ncols] for arr, ncols in self.data])
