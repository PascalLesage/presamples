from numpy.random import RandomState

# Max signed 32 bit integer, compatible with Windows
MAX_SIGNED_32BIT_INT = 2147483647


class Indexer(RandomState):
    """A (potentially) seeded integer RNG that remembers the generated index.

    Returns column indices for a sample array.

    ncols: Number of columns in the array for which a column index is returned.
    seed: Seed for RNG. Optional. If seed is "sequential", then starts counting from zero."""

    def __init__(self, ncols=0, seed=None):
        self.ncols = ncols
        self.seed_value, self.count, self.index = seed, 0, None
        super().__init__(None if seed == 'sequential' else seed)

    def __next__(self):
        self.count += 1
        if self.seed_value == 'sequential':
            self.index = self.count - 1
        else:
            self.index = self.randint(0, MAX_SIGNED_32BIT_INT) % self.ncols
        return self.index
