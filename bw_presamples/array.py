from numpy.random import RandomState
import numpy as np

# Max signed 32 bit integer, compatible with Windows
MAX_SIGNED_32BIT_INT = 2147483647


class IrregularPresamplesArray(RandomState):
    """A wrapper around a list of memory-mapped Numpy arrays with heterogeneous shapes.

    This class provides a simple way to consistently sample arrays with different shapes and datatypes.

    Input arguments:

    * ``filepaths``: An iterable of (Numpy array filepath, shape as tuple).
    * ``seed``: Seed for RNG. Optional. If seed is "sequential", then parameters will be sampled in order starting from the first one (index 0).

    """
    def __init__(self, filepaths, seed=None):
        if seed == "sequential":
            self.sequential, self.seed_value = True, None
        else:
            self.sequential, self.seed_value = False, seed
        super(IrregularPresamplesArray, self).__init__(self.seed_value)
        self.count = 0
        self.data = [
            (np.load(str(fp), mmap_mode='r'), shape[1])
            for fp, shape in filepaths
        ]

    def sample(self):
        """Draw a new sample from the pre-sample arrays"""
        if self.sequential:
            index = self.count
        else:
            index = self.randint(0, MAX_SIGNED_32BIT_INT)
        result = np.hstack([arr[:, index % ncols] for arr, ncols in self.data])
        self.count += 1
        return result
