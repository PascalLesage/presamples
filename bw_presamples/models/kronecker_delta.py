from .inventory_base import InventoryBaseModel
from stats_arrays import uncertainty_choices
import numpy as np


class KroneckerDelta(InventoryBaseModel):
    """A model that choose only one input from multiple possibilities at each iteration. All other possible inputs are set to zero. See `Kronecker delta functions <https://en.wikipedia.org/wiki/Kronecker_delta>`__.

    See documentation on ``InventoryBaseModel`` for how to specify ``exchanges``.

    If ``normalize`` is true, then the amount of the selected input is set to one (or minus one if negative). Otherwise, it is set the the original ``amount`` value.

    If ``equal_choice`` is true, then an input is selected with equal probability among all possible inputs. If false, then the absolute values of the amounts are used as weights.

    ``iterations`` is the number of Monte Carlo iterations to generate.

    Selection is made by choosing a random index between zero and ``len(exchanges)``. The value of this selector variable is stored in ``self.selector``.

    Currently, this class doesn't ensure that all inputs come from the same activity, or that the provided exchanges have any special type.

    """
    def __init__(self, exchanges, normalize=True, iterations=1000, equal_choice=False):
        self.data = self.find_exchanges(exchanges)
        self.iterations = iterations
        self.normalize = normalize
        self.equal_choice = equal_choice

    def run(self):
        self.matrix_array = np.zeros((len(self.data), self.iterations))
        amounts = np.array([o['amount'] for o in self.data])
        if self.equal_choice:
            p = None
        else:
            p = np.absolute(amounts) / np.absolute(amounts).sum()
        self.selector = np.random.choice(len(self.data), self.iterations, p=p)
        cols = np.arange(self.iterations)
        self.matrix_array[self.selector, cols] = 1
        if not self.normalize:
            self.matrix_array *= amounts.reshape((-1, 1))
        else:
            # Adjust sign as needed
            self.matrix_array[amounts < 0, :] *= -1

        return self.matrix_array
