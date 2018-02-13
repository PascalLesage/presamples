from .. import ParameterPresamples
from bw2data import projects
from bw2data.parameters import *
from bw2parameters import prefix_parameter_dict, substitute_in_formulas
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

        We need to traverse a directed acyclic graph; we choose an approach that is perhaps less efficient but easier to follow.

        Imagine our graph looks like the following:

        ::
                C - D ---------------
              /  \       \           \
             A -------- Database --- Project
              \    \     /           /
                B - E ---------------

        We can start with ``A``; we namespace the variables, and use ``dependency_chain`` to find out where all the other used parameters (in ``C``, ``B``, etc.) are. We can already namespace these as well, because we know their group name.

        ``dependency_chain`` also gives us a list of groups to traverse **in order**; we can then proceed group by group up the chain. The only tricky bit here would be to make sure we do things in the right order, but as we are using ``dependency_chain``, we are actually treating each activity group as its own graph, and so avoid any conflicts implicitly.

        Adds results to ``self.data`` and ``self.substitutions``. Doesn't return anything."""
        data, already = {}, set()
        groups, data = process_group(self.group, set())
        groups = groups.difference(set(self.global_params))
        while groups:
            new_groups, new_data = process_group(groups.pop(), already)
            groups = groups.union(new_groups).difference(set(self.global_params))
            data.update(new_data)

        self.data = data
        return self.data

        def process_group(group, already):
            """"""
            obj, kind = self._get_parameter_object(group)
            result = prefix_parameter_dict(obj.load(group), group)[0]
            if kind == 'project':
                return set(), result
            else:
                chain = obj.dependency_chain(group)
                substitutions = {
                    name: elem['group'] + '__' + name
                    for name in elem['names']
                    for elem in chain
                }
                return (
                    {o['group'] for o in chain}.difference(already),
                    substitute_in_formulas(result, substitutions)
                )

    def save_presample(self, name, append=True):
        """Save results to a presamples package.

        Will append to an existing package if ``append``; otherwise, raises an error if this package already exists."""
        pass

    def calculate_static(self, update_amounts=True):
        """Static calculation of parameter samples.

        Returns results (dictionary by parameter name). Also modifies ``amount`` field in-place if ``update_amounts``."""
        self._convert_amounts_to_floats()
        result = ParameterSet(
            self.data,
            self._flatten_global_params(self.global_params)
        ).evaluate()
        if update_amounts:
            for key, value in self.data.items():
                value['amount'] = result[key]
        return result

    def calculate_stochastic(self, iterations=1000, update_amounts=True):
        """Monte Carlo calculation of parameter samples.

        Returns Monte Carlo results (dictionary by parameter name). Also modifies ``amount`` field in-place if ``update_amounts``."""
        result = ParameterSet(
            self.data,
            self._flatten_global_params(self.global_params)
        ).evaluate_monte_carlo(iterations)
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

    def _flatten_global_params(self, gp):
        """Flatten nested dictionary of ``{group name: {name: data}}`` to ``{name: data}``.

        Assumes names are namespaced so there are no collisions."""
        return {y: z for v in gp.values() for y, z in v.items()}
