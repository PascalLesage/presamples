from .array import RegularPresamplesArrays
from .indexer import Indexer
from .utils import validate_presamples_dirpath, check_name_conflicts
from collections.abc import Mapping
from pathlib import Path
import json
import numpy as np
import os


class PresamplesPackage:
    """Interface for individual presample packages.

    Packages are directories, stored either locally or on a network resource (via `PyFilesystem <https://www.pyfilesystem.org/>`__.

    Presampled arrays are provided as a list of directory paths. Each directory contains a metadata file, and one or more data files:

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

    """
    def __init__(self, path):
        self.path = Path(path)
        validate_presamples_dirpath(path)
        self.indexer = Indexer(self.ncols, self.seed)
        next(self.indexer)

    @property
    def metadata(self):
        return json.load(open(self.path / "datapackage.json"))

    @property
    def name(self):
        return self.metadata['name']

    @property
    def seed(self):
        return self.metadata['seed']

    @property
    def ncols(self):
        return self.metadata['ncols']

    def change_seed(self, new):
        """Change seed to ``new``"""
        current = self.metadata
        current['seed'] = new
        with open(self.path / "datapackage.json", "w", encoding='utf-8') as f:
            json.dump(current, f, indent=2, ensure_ascii=False)

    @property
    def id(self):
        return self.metadata['id']

    @property
    def resources(self):
        return self.metadata['resources']

    def __len__(self):
        return len(self.resources)

    @property
    def parameters(self):
        if not hasattr(self, "_parameters"):
            self._parameters = ParametersMapping(self.path, self.resources, self.name, self.indexer)
        return self._parameters


class ParametersMapping(Mapping):
    def __init__(self, path, resources, package_name, sample_index=0):
        name_lists = [
            json.load(open(path / obj['names']['filepath'])) for obj in resources
        ]
        check_name_conflicts(name_lists)
        self.mapping = {
            name: (i, j)
            for i, lst in enumerate(name_lists)
            for j, name in enumerate(lst)
        }
        self.ipa = RegularPresamplesArrays([
            path / obj['samples']['filepath']
            for obj in resources
        ])
        self.ids = [(path, package_name, name) for name in self.mapping]

    def items(self):
        for key in self.mapping:
            yield (key, self[key])

    def values(self):
        for i, j in self.mapping.values():
            yield self.ipa.data[i][j, :]

    def __getitem__(self, key):
        i, j = self.mapping[key]
        return self.ipa.data[i][j, :]

    def __len__(self):
        return len(self.mapping)

    def __contains__(self, key):
        return key in self.mapping

    def __iter__(self):
        return iter(self.mapping)


class IndexedParametersMapping(ParametersMapping):
    """Like ``ParametersMapping``, but with a column index"""
    def __init__(self, path, resources, package_name, sample_index=0):
        super().__init__(path, resources, package_name)
        self.index = sample_index

    # Changing the Indexer.index value changes the object, meaning our reference
    # will break. So we need to pass the Indexer object and lookup the `index`
    # value dynamically
    def _get_index(self):
        if isinstance(self.__index, Indexer):
            return self.__index.index
        else:
            return self.__index

    def _set_index(self, value):
        self.__index = value

    index = property(_get_index, _set_index)

    def values(self):
        return (float(x) for x in self.array)

    @property
    def array(self):
        return self.ipa.sample(self.index)

    def __getitem__(self, key):
        array = super().__getitem__(key)
        return float(array[self.index])
