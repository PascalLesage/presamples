from numpy.random import RandomState
import numpy as np

# Max signed 32 bit integer, compatible with Windows
MAX_SIGNED_32BIT_INT = 2147483647


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
            (np.load(str(fp), mmap_mode='r'), shape[1])
            for fp, shape in filepaths
        ]

    def sample(self):
        """Draw a new sample from the pre-sample arrays"""
        index = self.randint(0, MAX_SIGNED_32BIT_INT)
        return np.hstack([arr[:, index % ncols] for arr, ncols in self.data])
