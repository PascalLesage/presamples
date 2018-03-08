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
    """Model that samples and calculates parameterized datasets from Brightway2 data.

    This model takes one input, ``group``, the name of the group of parameters to load. The model will load this group and all other groups needed in its dependency chain.

    Normally the entire dependency chain will be freshly calculated. However, you can load parameter values that have been calculated in another model run using the ``load_existing`` function. The ``load_existing`` function **does not** copy values from an existing package, if just makes these values available during calculations.

    TODO: Explain this better, including gotchas.

    Because parameter names can overlap from group to group, we change the parameter names by append the group name followed by the string "__". For example, parameter "foo" from group "bar" would become "bar__foo".

    Model runs can be either static (one new set of values produced) or stochastic (many new values produced) - the corresponding methods are ``calculate_static`` and ``calculate_stochastic``. A static calculation will just reproduce what is already in your database, so the normal use case is to alter one of the named parameters, and then recalculate the dependency chain.

    Both calculation methods only generate new values for the named parameters. To values that can be inserted into an LCA matrix, your ``group`` should have some activated exchanges, and you need to call ``calculate_matrix_presamples``.

    Use either ``save_presample`` (for a new presample package) or ``append_presample`` (to add to an existing presample package) to save model results. Be aware that presample packages can't have duplicate named parameters, so appending to an existing package where even one of the named parameters already exists will raise an error."""
    def __init__(self, group):
        self.group = group
        self.obj, self.kind = self._get_parameter_object(group)
        self.global_params = {}
        self.data = {}
        self.matrix_data = []

    def load_existing(self, fp, only=None):
        """Add existing parameter presamples to ``self.global_params``.

        ``only`` is an optional list of parameter names to filter; if provided, all other names are ignored.
        """
        for key, value in PresamplesPackage(fp).parameters.items():
            if only and key not in only:
                continue
            if key in self.global_params:
                warnings.warn("Replacing existing named parameter: {}".format(key))
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

        We can start with ``A``; we namespace the variables, and use ``dependency_chain`` to find out where all the other used parameters (in ``C``, ``B``, etc.) are. We can already namespace these as well, because we know their group name. The tricky part is that we need to get the dependencies or the dependencies, even if they aren't directly required by the original group.

        ``dependency_chain`` gives us a list of groups to traverse **in order**; we can then proceed group by group up the chain. The only tricky bit here would be to make sure we do things in the right order, to avoid "missing" dependent groups. As we are using ``dependency_chain``, we are actually treating each activity group as **its own graph**, and so avoid any conflicts implicitly.

        Adds results to ``self.data`` and ``self.substitutions``. Doesn't return anything."""
        self.groups = set([self.group])
        groups, data = self._process_group(self.group)
        while groups:
            this_group = groups.pop()
            self.groups.add(this_group)
            new_groups, new_data = self._process_group(this_group)
            groups = groups.union(new_groups).difference(self.groups)
            data.update(new_data)

        # Purge any individual parameters which were already defined in
        # self.global_params. This can occur if a presample includes part of
        # a group - we keep the "fixed" values. The presamples library doesn't
        # include any functions that allow for partial inclusion, but who knows
        # what users will do.
        # TODO: Make sure this behaviour is documented and explained!
        self.data = {k: v for k, v in data.items() if k not in self.global_params}

        return self.data

    def _process_group(self, group):
        """Load namespaced data for this group, including dependent variables, while ignoring variables already defined in ``global_params``.

        Returns a set of group names to traverse and a dictionary of named parameters and values."""
        obj, kind = self._get_parameter_object(group)
        # Loads just parameters from this group
        result = prefix_parameter_dict(obj.load(group), group + "__")[0]
        if kind == 'project':
            # Not different logic, just shortcut
            return set(), result
        else:
            chain = obj.dependency_chain(group)
            substitutions = {
                name: elem['group'] + '__' + name
                for elem in chain
                for name in elem['names']
            }
            # Substitute the variable references applicable *for this group*.
            # In another group, the same named variable could refenence
            # something else.
            results = substitute_in_formulas(result, substitutions)
            # For each new group, check if **all** parameters are defined in
            # ``global_params``
            new = {o['group'] for o in chain
                   if {substitutions[name] for name in o['names']
                       }.difference(set(self.global_params))
                   }
            return new, results

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
            self.global_params
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
            self.global_params
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
            self.global_params
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
