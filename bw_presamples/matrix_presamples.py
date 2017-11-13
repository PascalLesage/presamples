from .array import IrregularPresamplesArray
from bw2calc.indexing import index_with_arrays as _
from bw2calc.matrices import TechnosphereBiosphereMatrixBuilder as MB
from bw2calc.utils import md5
from pathlib import Path
import itertools
import json
import numpy as np
import os
import wrapt


@wrapt.decorator
def nonempty(wrapped, instance, args, kwargs):
    """Skip function execution if there are no presamples"""
    if instance.empty:
        return
    else:
        return wrapped(*args, **kwargs)


class MatrixPresamples(object):
    """Efficiently map presampled arrays and insert their values into LCA matrices.

    Presampled arrays are provided as a list of directory paths. Each directory contains a datapackage file:

    * ``datapackage.json``: A JSON file following the `datapackage standard <http://frictionlessdata.io/guides/data-package/>`__ that indicates the provenance of the data. The specific content of the datapackage will depend on what the presamples contains.
    All datapackage.json files should minimally have the following information:

    .. code-block:: json

        {
          "name": human readable name,
          "id": uuid,
          "profile": "data-package",
          "resources": [{
                "type": string,
                "samples": {
                    "filepath": "{id}.{data package index}.samples.npy",
                    "md5": md5 hash,
                    "shape": [rows, columns],
                    "dtype": dtype
                },
                "indices": {
                    "filepath": "{id}.{data package index}.indices.npy",
                    "md5": md5 hash
                },
                "matrix": string,
                "row from label": string,
                "row to label": string,
                "row dict": string,
                "col from label": string,
                "col to label": string,
                "col dict": string,
                "profile": "data-resource",
                "format": "npy",
                "mediatype": "application/octet-stream"
            }]
        }

    The ``resources`` list should have at least one resource. Multiple resources of different types can be present in a single datapackage. The field ``{data package index}`` doesn't have to be consecutive integers, but should be unique for each resource. If there is only one set of samples, it can be omitted entirely.

    The presamples directory will contain the following two files for each resource:

    * ``{uuid}.{data package index}.samples.npy``: Array of samples values in `npy format <https://docs.scipy.org/doc/numpy-dev/neps/npy-format.html>`__.
    * ``{uuid}.{data package index}.indices.npy``: A Numpy `record array <https://docs.scipy.org/doc/numpy/reference/generated/numpy.recarray.html>`__ in ``npy`` format with something like the following columns:
        * ``input``: uint32
        * ``output``: uint32
        * ``row``: uint32
        * ``col``: uint32
        * ``type``: uint8

    The columns above are for technosphere and biosphere samples, there can be small modifications for other types of samples. For example, characterization factors would normally have the columns "flow" and "row".

    For technosphere samples, ``type`` is an integer from ``bw2data.utils.TYPE_DICTIONARY`` that indicates whether the modified exchange is an consumer or producer.

    The metadata is loaded and concatenated. Input and output values for LCA matrix elements are mapped to the correct row and column indices.

    The samples arrays are not loaded into memory, but memory mapped to reduce resource consumption. As such, they are not concatenated.

    Normal life cycle for this class:

    * Instantiate with some directory paths and (optionally) a random seed; load data.
    * After building an LCA object, map the index arrays with ``index_arrays`` from integer ids to matrix rows and columns.
    * Before a static calculation, or for each Monte Carlo iteration, update the relevant matrices using the ``update_matrices`` function.

    Note that we currently assume that all index values will be present in the built matrix. Silent errors or losses in efficiency could happen if this assumption does not hold!

    """
    def __init__(self, dirpaths, seed=None):
        self.seed = seed

        self.data = []
        for dirpath in (dirpaths or []):
            self.validate_dirpath(Path(dirpath))
            self.data.extend(self.load_data(Path(dirpath), seed))

        self.empty = not bool(self.data)

    @staticmethod
    def validate_dirpath(dirpath):
        """Check that a ``dirpath`` has a valid `datapackage.json` file and data files with matching hashes."""
        assert os.path.isdir(dirpath)
        files = list(os.listdir(dirpath))
        assert "datapackage.json" in files, "{} missing a datapackage file".format(dirpath)
        metadata = json.load(
            open(dirpath / "datapackage.json"),
            encoding="utf-8"
        )
        for resource in metadata['resources']:
            assert os.path.isfile(dirpath / resource['samples']['filepath'])
            assert md5(dirpath / resource['samples']['filepath']) == \
                resource['samples']['md5']
            assert os.path.isfile(dirpath / resource['indices']['filepath'])
            assert md5(dirpath / resource['indices']['filepath']) == \
                resource['indices']['md5']

    @classmethod
    def load_data(cls, dirpath, seed):
        """Load data and metadata from a directory.

        This function will consolidate presamples with the same type. We check to make sure the relevant metadata (e.g. row and column labels) is identical when doing such consolidation.

        Will also instantiate ``IrregularPresamplesArray`` objects.

        Returns a dictionary with a list of resources:

        ..code-block:: python

            {
                'name': name,
                'id': uuid,
                'resources': [{
                    'type': string,
                    'samples': IrregularPresamplesArray instance,
                    'indices': Numpy array,
                    'matrix': string,
                    "row from label": string,
                    "row to label": string,
                    "row dict": string,
                    "col from label": string,
                    "col to label": string,
                    "col dict": string,
                }]
            }

        """
        metadata = json.load(
            open(dirpath / "datapackage.json"),
            encoding="utf-8"
        )
        results = {
            'name': metadata['name'],
            'id': metadata['id'],
            'resources': []
        }
        fltr = lambda x: x['type']
        resources = metadata["resources"]
        resources.sort(key=fltr)

        for key, group in itertools.groupby(resources, fltr):
            group = cls.consolidate(dirpath, seed, list(group))
            results.append(group)

        return results

    @staticmethod
    def consolidate(dirpath, seed, group):
        # Check that metadata is the same
        assert len({el['matrix'] for el in group}) == 1, "Conflicting matrices"
        assert len({
            (el['row from label'], el['row to label']m el['row dict'])
            for el in group
        }) == 1, "Conflicting labels"
        if any(['col dict' in o for o in group]):
            assert len({
                (el['col from label'], el['col to label']m el['col dict'])
                for el in group
            }) == 1, "Conflicting labels"

        indices = [np.load(dirpath / r['indices']['filepath']) for r in group]
        # Check that indices have right shape
        assert len({o.shape[1] for o in indices}) == 1, "Conflicting index shapes"
        indices = np.hstack(indices)
        samples = IrregularPresamplesArray([
            (dirpath / el['samples']['filepath'], el['samples']['shape'])
            for el in group
        ])

        SKIP = ('indices', 'samples', 'profile', 'format', 'mediatype')
        result = {k: v for k, v in group[0].items() if k not in SKIP}
        result.update({'samples': samples, 'indices': indices})
        return result

    @nonempty
    def index_arrays(self, lca):
        for elem in self.data:
            _(
                getattr(elem['indices'], elem['row from label']),
                getattr(elem['indices'], elem['row to label']),
                getattr(lca, elem['row dict'])
            )
            if "col dict" in elem:
                _(
                    getattr(elem['indices'], elem['col from label']),
                    getattr(elem['indices'], elem['col to label']),
                    getattr(lca, elem['col dict'])
                )

    @nonempty
    def update_matrices(self, lca):
        for elem in self.data:
            sample = elem['sampler'].sample()
            if elem['type'] == 'technosphere':
                MB.fix_supply_use(elem['indices'], sample)
            matrix = getattr(lca, elem['matrix'])
            if 'col dict' in elem:
                matrix[
                    getattr(elem['indices'], elem['row to label']),
                    getattr(elem['indices'], elem['col to label']),
                ] = sample
            else:
                matrix[
                    getattr(elem['indices'], elem['row to label']),
                    getattr(elem['indices'], elem['row to label']),
                ] = sample