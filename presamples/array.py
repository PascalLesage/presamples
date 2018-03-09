import numpy as np


class RegularPresamplesArrays:
    """A wrapper around a list of memory-mapped Numpy arrays with heterogeneous shapes.

    This class provides a simple way to consistently multiple arrays with the same number of columns.

    Input arguments:

    * ``filepaths``: An iterable of Numpy array filepaths.

    """
    def __init__(self, filepaths):
        self.count = 0
        self.data = [
            np.load(str(fp), mmap_mode='r')
            for fp in filepaths
        ]
        self.start_indices = np.cumsum([0] + [array.shape[0] for array in self.data])

    def sample(self, index):
        """Draw a new sample from the pre-sampled arrays"""
        result = np.hstack([arr[:, index] for arr in self.data])
        self.count += 1
        return result

    def translate_row(self, row):
        """Translate row index from concatenated array to (array list index, row modulo)

        TODO: Test"""
        i = np.searchsorted(self.start_indices, row)
        return (i, row - self.start_indices[i])
