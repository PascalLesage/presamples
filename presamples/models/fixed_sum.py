from .inventory_base import InventoryBaseModel
from stats_arrays import uncertainty_choices
import numpy as np


class FixedSum(InventoryBaseModel):
    """Model where all exchanges sum to a certain amount.

    See documentation on ``InventoryBaseModel`` for how to specify ``exchanges``.

    ``expected_sum`` should only be used of the sum is different than the current sum of the ``amount`` values.

    ``iterations`` is the number of Monte Carlo iterations to generate.

    ``rescale_fixed`` will also scale exchanges with no uncertainty; default is ``False``, i.e. exchanges without uncertainty won't be changed.

    Note that ``expected_sum`` can't be used when ``rescale_fixed`` is ``False``, because they have weird interaction effects.

    Currently, this class doesn't ensure that all inputs come from the same activity, or that the provided exchanges have any special type.

    """
    def __init__(self, exchanges, expected_sum=None, iterations=1000, rescale_fixed=False):
        if not rescale_fixed and expected_sum:
            raise ValueError("Please choose either `rescale_fixed` or `expected_sum`")

        self.data = self.find_exchanges(exchanges)
        for obj in self.data:
            self.fill_uncertainty(obj)
        self.iterations = iterations
        self.expected = expected_sum or sum(o['amount'] for o in self.data)
        if rescale_fixed:
            self.mask = np.array([True for _ in self.data])
        else:
            self.mask = np.array([obj['uncertainty type'] not in (0, 1) for obj in self.data])

    def fill_uncertainty(self, obj):
        """Add default uncertainty values if missing"""
        if "uncertainty type" not in obj:
            obj['uncertainty type'] = 0
        if 'loc' not in obj:
            obj['loc'] = obj['amount']

    def random_sample(self, exc):
        """Draw a random sample from this exchange."""
        ut = uncertainty_choices[exc.get("uncertainty type", 0)]
        array = ut.from_dicts(exc)
        return ut.bounded_random_variables(array, self.iterations)

    def run(self):
        self.matrix_array = np.vstack([self.random_sample(o) for o in self.data])
        scale = ((self.expected - self.matrix_array[~self.mask, :].sum(axis=0)) /
                 self.matrix_array[self.mask, :].sum(axis=0))
        self.matrix_array[self.mask, :] *= scale
        return self.matrix_array


