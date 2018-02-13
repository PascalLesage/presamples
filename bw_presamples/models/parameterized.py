from .. import ParameterPresamples
from bw2data import projects
from bw2data.parameters import *
from bw2parameters import *
import os


class ExpiredGroup(Exception):
    pass


class ParameterizedBrightwayModel:
    def __init__(self, group):
        self.group = group
        self.obj, self.kind = self._get_parameter_object(group)
        self.global_params = {}
        self.data = {}
        self.substitutions = {}

    def load_existing(self, fp):
        """Add existing parameter presamples to ``self.global_params``."""
        # Correct filepath using projects directory, if necessary
        existing = ParameterPresamples(fp)
        # Load data into ``global_params``

    def load_parameter_data(self):
        """Load all necessary parameter data from group ``self.group``.

        Traverses dependency chain. Namespaces all parameters names by prefixes the name of their group.

        Will use any existing data, if available (i.e. if loaded already using ``load_existing``).

        Adds results to ``self.data`` and ``self.substitutions``. Doesn't return anything."""
        pass

    def save_presample(self, name, append=True):
        """Save results to a presamples package.

        Will append to an existing package if ``append``; otherwise, raises an error if this package already exists."""
        pass

    def calculate_static(self, update_amounts=True):
        """Static calculation of parameter samples.

        Returns results (dictionary by parameter name). Also modifies ``amount`` field in-place if ``update_amounts``."""
        self._convert_amounts_to_floats()
        result = ParameterSet(self.data, self.global_params).evaluate()
        if update_amounts:
            for key, value in self.data.items():
                value['amount'] = result[key]
        return result

    def calculate_stochastic(self, iterations=1000, update_amounts=True):
        """Monte Carlo calculation of parameter samples.

        Returns Monte Carlo results (dictionary by parameter name). Also modifies ``amount`` field in-place if ``update_amounts``."""
        result = ParameterSet(self.data, self.global_params).evaluate_monte_carlo(iterations)
        if update_amounts:
            for key, value in self.data.items():
                value['amount'] = result[key]
        return result

    def _convert_amounts_to_floats(self):
        """Make sure all ``amount`` values are floats and not Numpy arrays.

        Modifies in-place; doesn't return anything."""
        for obj in self.data.values():
            obj['amount'] = float(obj['amount'])

    def _convert_amounts_to_array(self):
        pass

    def _get_parameter_object(self, group):
        # Check to make sure group exists
        Group.get(name=group)

        # Need everything fresh to get correct dependency chain
        if not Group.get(name=group).fresh:
            raise ExpiredGroup(
                "Please recalculate this group before using it in parameterized models"
            )

        if group == 'project':
            return ProjectParameter, 'project'
        elif group in databases:
            return DatabaseParameter, 'database'
        else:
            return ActivityParameter, 'activity'
