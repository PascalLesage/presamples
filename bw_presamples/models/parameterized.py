from .. import PresamplesPackage
from ..packaging import (
    append_presamples_package,
    create_presamples_package,
    split_inventory_presamples,
    to_2d,
    to_array,
)
from bw2data import projects
from bw2data.backends.peewee.schema import ExchangeDataset
from bw2data.parameters import *
from bw2parameters import (
    FormulaSubstitutor,
    prefix_parameter_dict,
    substitute_in_formulas,
)
import numpy as np
import os
import warnings


class ExpiredGroup(Exception):
    pass


class ParameterizedBrightwayModel:
    def __init__(self, group):
        self.group = group
        self.obj, self.kind = self._get_parameter_object(group)
        self.global_params = {}
        self.data = {}
        self.matrix_data = []

    def load_existing(self, fp, labels=None):
        """Add existing parameter presamples to ``self.global_params``."""
        for key, value in ParameterPresamples(fp, labels=labels).items():
            if key in self.global_params:
                warnings.warn("Replacing existing parameter group: {}".format(key))
            self.global_params[key] = value

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
        def process_group(group, already):
            """Load namespaced data for this group, including dependent variables."""
            obj, kind = self._get_parameter_object(group)
            result = prefix_parameter_dict(obj.load(group), group + "__")[0]
            if kind == 'project':
                return set(), result
            else:
                chain = obj.dependency_chain(group)
                substitutions = {
                    name: elem['group'] + '__' + name
                    for elem in chain
                    for name in elem['names']
                }
                results = substitute_in_formulas(result, substitutions)
                new = {o['group'] for o in chain
                       if {substitutions[name]
                           for name in o['names']}.difference(already)
                       }
                return new, results

        data = {}
        already = {key for obj in self.global_params.values() for key in obj}
        groups, data = process_group(self.group, already)
        groups = groups.difference(set(self.global_params))
        while groups:
            new_groups, new_data = process_group(groups.pop(), already)
            groups = groups.union(new_groups).difference(set(self.global_params))
            data.update(new_data)

        # Purge any individual parameters which were already defined in
        # self.global_params. This can occur if a presample includes part of
        # a group - we keep the "fixed" values.
        # TODO: Make sure this behaviour is documented and explained!
        data = {k: v for k, v in data.items() if k not in already}

        self.data = data
        return self.data

    def append_presample(self, dirpath, label):
        """Append presample to an existing presamples package.

        ``dirpath`` is the location of an existing presamples package. ``label`` is the label for this section of presamples.

        Returns directory path of the modified presamples package."""
        array = self._convert_amounts_to_array()
        return append_presamples_package(
            matrix_data=self.matrix_data,
            parameter_data=[(array, sorted(self.data), label)],
            dirpath=dirpath
        )

    def save_presample(self, label, name=None, id_=None, dirpath=None):
        """Save results to a presamples package.

        Will append to an existing package if ``append``; otherwise, raises an error if this package already exists."""
        array = self._convert_amounts_to_array()
        return create_presamples_package(
            matrix_data=self.matrix_data,
            parameter_data=[(array, sorted(self.data), label)],
            name=name,
            id_=id_,
            dirpath=dirpath,
        )

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

    def calculate_matrix_presamples(self):
        """Calculate matrix presamples for an activated exchanges (``ParameterizedExchange``) linked to ``self.group``.

        You should have already done ``calculate_static`` or ``calculate_stochastic``.

        Populates ``self.matrix_data``, and returns a dictionary of ``{exchange id: numeric value}``."""
        assert self.data, "Must load parameter data before using this method"

        substitutor = FormulaSubstitutor({v['original']: k for k, v in self.data.items()})

        interpreter = ParameterSet(
            self.data,
            self._flatten_global_params(self.global_params)
        ).get_interpreter(evaluate_first=False)
        queryset = ParameterizedExchange.select().where(
            ParameterizedExchange.group == self.group
        )
        results = {obj.exchange: interpreter(substitutor(obj.formula))
                   for obj in queryset}

        samples, indices = [], []
        queryset = ExchangeDataset.select().where(
            ExchangeDataset.id << tuple(results)
        )

        for obj in queryset:
            samples.append(np.array(results[obj.id]).reshape(1, -1))
            indices.append((
                (obj.input_database, obj.input_code),
                (obj.output_database, obj.output_code),
                obj.type
            ))

        self.matrix_data = split_inventory_presamples(np.vstack(samples), indices)
        return results

    def _convert_amounts_to_floats(self):
        """Make sure all ``amount`` values are floats and not Numpy arrays.

        Modifies in-place; doesn't return anything."""
        for obj in self.data.values():
            obj['amount'] = float(obj['amount'])

    def _convert_amounts_to_array(self):
        return np.vstack([to_2d(to_array(self.data[key]['amount']))
                          for key in sorted(self.data)])

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
