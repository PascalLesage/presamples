from .array import RegularPresamplesArrays
from .errors import IncompatibleIndices, ConflictingLabels
from .indexer import Indexer
from .package_interface import IndexedParametersMapping
from .utils import validate_presamples_dirpath
from pathlib import Path
import itertools
import json
import numpy as np
import wrapt
from collections.abc import Sequence, Mapping
from collections import defaultdict
import copy

@wrapt.decorator
def nonempty(wrapped, instance, args, kwargs):
    """Skip function execution if there are no presamples"""
    if instance.empty:
        return
    else:
        return wrapped(*args, **kwargs)

class PackagesDataLoader:
    """Load set of presample packages and ready underlying data for use

    Named parameters found in presample packages will be assembled into a
    ``ConsolidatedIndexedParameterMapping``, accessed through the ``parameters``
    property.

    Matrix data found in presample packages are readied to be mapped and
    inserted into LCA matrices using the corresponding methods.

    In both cases, elements (named parameter or matrix element) repeated in
    multiple presample packages will take the value (and the ``Indexer``)
    of the last presample package in the list that contains data on the element.

    Parameters
    ----------
    dirpaths : iterable of paths to presample packages
        See notes below for information on expected contents of directories.
    seed :  {None, int, array_like, "sequential"}, optional
        Seed value to use for index RNGs. Default is to use the seed values in
        each package, only specify this if you want to override the default.
    lca : Brightway2 LCA object
        Used when ``PackagesDataLoader`` instantiated from LCA (or
        MonteCarloLCA) object.

    Notes
    -----
    1. Accessing and using loaded named parameters

    The returned ``PackagesDataLoader`` instance allows access to loaded
    parameter data via the ``parameters`` property.

    2. Using loaded matrix data in LCA

    When used for LCA within the Brightway2 framework, the
    ``PackagesDataLoader`` instance is an attribute of the ``LCA``
    (or ``MonteCarloLCA``) instance. The ``LCA`` instance will call the method
    ``index_arrays`` in order to identify the matrix indices of values that
    will be overwritten, and the ``update_matrices`` method to update values.

    Warning
    -------
    The order of the passed presample package dirpaths is key! Every matrix
    element or named parameter that is repeated in multiple presample
    packages will take the value of the *last* presample package that is passed.
    All former values will not be used.

    Warning
    -------
    Note that we currently assume that all index values in matrix data will be
    present in the built matrices of the LCA instance. Silent errors or losses
    in efficiency could happen if this assumption does not hold.
    """
    def __init__(self, dirpaths, seed=None, lca=None):
        """Load parameter and matrix data from list presamples package paths"""
        self.seed, self.dirpaths = seed, dirpaths
        self.matrix_data_loaded, self.parameter_data_loaded = [], []
        self.package_indexers, self.matrix_indexer = [], []
        self.lca_reference = lca

        for dirpath in (dirpaths or []):
            validate_presamples_dirpath(Path(dirpath))
            # Even empty presamples have name and id
            section = self.load_data(Path(dirpath), self.seed)
            self.package_indexers.append(section['indexer'])
            if section["matrix-data"]:
                self.matrix_data_loaded.append(
                    {k:v for k, v in section.items()
                     if k!='parameter-data'}
                )
                self.matrix_indexer.append(section['indexer'])
            if section['parameter-data']:
                self.parameter_data_loaded.append(
                    {k:v for k, v in section.items()
                     if k!='matrix-data'}
                )

        # Used for LCA classes; can skip matrix manipulation if no matrix data
        self.empty = not bool(self.matrix_data_loaded)

        # Advance to first position on the indices
        self.update_package_indices()

    def __str__(self):
        return "PackagesDataLoader with {} packages:{}".format(
            len(self.dirpaths), ["\n\t{}".format(o) for o in self.dirpaths]
        )

    def __len__(self):
        """ Return the number of presample packages used to build the loader"""
        return len(self.dirpaths)

    @classmethod
    def load_data(cls, dirpath, seed=None):
        """Load data and metadata from a directory containing a presamples package

        Parameters
        ----------
        dirpath: str or Pathlike object
            path to a presamples package
        seed: {None, int, array_like, "sequential"}, optional
            Only specify this if you want to override seed value in
            presamples package.

        Returns
        -------
        dict
            Dictionary with loaded data
        """
        metadata = json.load(
            open(dirpath / "datapackage.json")
        )
        get_seed = lambda x: seed if seed is not None else x
        data = {
            'name': metadata['name'],
            'path': dirpath,
            'id': metadata['id'],
            'seed': metadata['seed'],
            'ncols': metadata['ncols'],
            'matrix-data': [],
            'parameter-data': [],
            # Set default ncols if package is empty
            'indexer': Indexer(metadata['ncols'] or 1, get_seed(metadata['seed']))
        }
        matrix_resources = [
            obj for obj in metadata["resources"] if obj.get('matrix')
        ]
        fltr = lambda x: x['type']
        matrix_resources.sort(key=fltr)
        for key, group in itertools.groupby(matrix_resources, fltr):
            group = cls.consolidate(dirpath, list(group))
            data['matrix-data'].append(group)

        parameter_resources = [
            obj for obj in metadata['resources'] if obj.get('names')
        ]

        data['parameter-data'] = IndexedParametersMapping(
            path=data['path'],
            resources=parameter_resources,
            package_name=data['name'],
            sample_index=data['indexer']
        )
        return data

    @staticmethod
    def consolidate(dirpath, group):
        """Add together indices and samples in the same presamples package if they have the same type.

        Consolidating is not necessary for the functionality of this class, but it does make it easier to do things like sensitivity analysis afterwards."""
        # Check that metadata is the same
        assert len({el['matrix'] for el in group}) == 1, "Conflicting matrices"
        if not len({
                    (el['row from label'], el['row to label'], el['row dict'])
                    for el in group
                }) == 1:
            raise ConflictingLabels
        if any(['col dict' in o for o in group]):
            if not len({
                        (el['col from label'], el['col to label'], el['col dict'])
                        for el in group
                    }) == 1:
                raise ConflictingLabels

        indices = [np.load(dirpath / r['indices']['filepath']) for r in group]
        # Check that indices have right shape
        if not len({o.dtype for o in indices}) == 1:
            raise IncompatibleIndices
        indices = np.hstack(indices)
        samples = RegularPresamplesArrays([
            (dirpath / el['samples']['filepath'])
            for el in group
        ])

        SKIP = ('indices', 'samples', 'profile', 'format', 'mediatype')
        result = {k: v for k, v in group[0].items() if k not in SKIP}
        result.update({'samples': samples, 'indices': indices})
        return result

    @nonempty
    def index_arrays(self, lca):
        """Add row and column values to the indices.

        As this function can be called multiple times, we check for each element
        if it has already been called, and whether the required mapping
        dictionary is present."""

        from bw2calc.indexing import index_with_arrays

        for obj in self.matrix_data_loaded:
            for elem in obj["matrix-data"]:
                # Allow for iterative indexing, starting with inventory
                if elem.get('indexed'):
                    # Already indexed
                    continue
                elif not hasattr(lca, elem['row dict']):
                    # This dictionary not yet built
                    continue
                elif "col dict" in elem and not hasattr(lca, elem['col dict']):
                    # This dictionary not yet built
                    continue

                index_with_arrays(
                    elem['indices'][elem['row from label']],
                    elem['indices'][elem['row to label']],
                    getattr(lca, elem['row dict'])
                )
                if "col dict" in elem:
                    index_with_arrays(
                        elem['indices'][elem['col from label']],
                        elem['indices'][elem['col to label']],
                        getattr(lca, elem['col dict'])
                    )
                elem['indexed'] = True

    @nonempty
    def update_matrices(self, lca=None, matrices=None, advance_indices=True):
        """Update the LCA instance matrices from presamples"""
        from bw2calc.matrices import TechnosphereBiosphereMatrixBuilder as MB

        lca = self.lca_reference if lca is None else lca
        if lca is None:
            raise ValueError("Must give LCA on instantiation or in this method")

        if matrices is None and advance_indices:
            # Advance all the indexers
            self.update_package_indices()

        for indexer, obj in zip(self.matrix_indexer, self.matrix_data_loaded):
            for elem in obj["matrix-data"]:
                try:
                    matrix = getattr(lca, elem['matrix'])
                except AttributeError:
                    # This LCA doesn't have this matrix
                    continue

                if elem['matrix'] == 'technosphere_matrix':
                    # Remove existing matrix factorization
                    # because changing technosphere
                    if hasattr(lca, "solver"):
                        delattr(lca, "solver")

                if matrices is not None and elem['matrix'] not in matrices:
                    continue

                sample = elem['samples'].sample(indexer.index)
                if elem['type'] == 'technosphere':
                    MB.fix_supply_use(elem['indices'], sample)
                if 'col dict' in elem:
                    matrix[
                        elem['indices'][elem['row to label']],
                        elem['indices'][elem['col to label']],
                    ] = sample
                else:
                    # filter elementary flows not in database
                    mask = np.isin(elem['indices'][elem['row to label']],matrix.indices)
                    existing = elem['indices'][elem['row to label']][mask]
                    matrix[
                        existing,
                        existing,
                    ] = sample[mask]

    def update_package_indices(self):
        """Move to next index"""
        for indexer in self.package_indexers:
            next(indexer)

    def reset_sequential_indices(self):
        """Reset all sequential indexers.

        Needed for Monte Carlo calculations."""
        for indexer in self.package_indexers:
            indexer.reset_sequential_indices()

    @property
    def parameters(self):
        """Consolidated access to all named parameters

        See ``ConsolidatedIndexedParameterMapping`` for notes on consolidation.
        """
        if not hasattr(self, "_parameters"):
            self._parameters = ConsolidatedIndexedParameterMapping(
                [
                    obj['parameter-data']
                    for obj in self.parameter_data_loaded
                ]
            )
        return self._parameters

class ConsolidatedIndexedParameterMapping(Mapping):
    """ Interface for consolidated named parameters in set of presample packages

    Map all named parameters in a list of IndexedParameterMapping objects to
    presample arrays and Indexers identified in the **last** presample package
    that contains data on the named parameter.

    This allows named parameters to be overwritten by successive presample
    packages.

    Typically called directly from a :class:`PackagesDataLoader` instance.

    Parameters
    ----------
    list_IPM : list
        List of IndexedParameterMapping objects. The IndexedParameterMapping
        (IPM) objects are typically created by a ``PackagesDataLoader`` instance.

    Important
    ---------
        The order of the IPMs is crucial, as named parameters in later
        IPMs overwrites data from earlier IMPs.

    Notes
    -----
    The CIPM instance can be used to access the following properties:

    - ``names``: names of all *n* named parameters
    - ``ipm_mapper``: dict {parameter name: IndexedParameterMapping},
      identifying the IndexedParameterMapping used for a given
      named parameter.
    - ``consolidated_array``: array of shape (n,) values, giving access
      to the values for the *n* named parameters
    - ``consolidated_index``: array of shape (n,) values, giving access
      to the index values for the *n* named parameters in their
      respective IndexedParameterMapping
    - ``ids``: dict of format {named parameters: ids}, where ``ids``
      are tuples of (presamples package path, presamples package name,
      name of parameter). ``ids`` only contains information about the
      *last* presamples package with data on the named parameter.
    - ``replaced``: dict of format {named parameters: ids of presample
      packages that were overwritten}
    """

    def __init__(self, list_IPM):
        """Init a ConsolidatedIndexedParameterMapping from a list of IndexedParameterMapping"""
        self.ipms = list_IPM
        assert all([
            isinstance(ipm, IndexedParametersMapping)
            for ipm in self.ipms
        ])

        self._consolidate_ipms()

    def __len__(self):
        """ Return the number of unique named parameters"""
        return len(self.names)

    def __getitem__(self, name):
        """Return value for given parameter, at current index in corresponding IPM"""
        i = self.names.index(name)
        return self.consolidated_array[i]

    def __iter__(self):
        """Iterate through unique parameter names"""
        return iter(self.names)


    def _consolidate_ipms(self):
        """Map parameter names to source package and values"""
        self.names = []
        self.ids = {}
        self.ipm_mapper = {}
        self.replaced = defaultdict(list)
        for i, ipm in enumerate(self.ipms):
            for n, name in enumerate(ipm.names):
                if name not in self.names:
                    self.names.append(name)
                else:
                    old_ipm = self.ipms[self.ipm_mapper[name]]
                    ind_index = list(old_ipm.mapping.keys()).index(name)
                    self.replaced[name].append((old_ipm.ids[ind_index][0], old_ipm.ids[ind_index][1]))
                self.ids[name] = ipm.ids[n]
                self.ipm_mapper[name] = i

    @property
    def consolidated_indices(self):
        """ Return the index value for the IndexedParameterMapping used for each name"""
        return [self.ipms[self.ipm_mapper[name]].index for name in self.names]

    @property
    def consolidated_array(self):
        """ Array of values for named parameter

        Each value is taken from the last IndexedParameterMapping object that
        contains data on the named parameter.
        The used IndexedParameterMapping contains information about the path
        to the presamples array, the corresponding mapping for the named
        parameter and the current Indexer value.
        """
        arr = np.empty(shape=(len(self.names)))
        for i, name in enumerate(self.names):
            arr[i] = self.ipms[self.ipm_mapper[name]][name]
        return arr
