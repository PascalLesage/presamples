from .utils import validate_presamples_dirpath
from collections.abc import Mapping
from pathlib import Path
import json
import numpy as np
import os


class NameConflicts(Exception):
    """Can't flatten dictionary due to conflicting parameter names"""
    pass


class PresamplesPackage:
    """Base class for presample packages.

    Provides methods common to all presample package classes."""

    """Base class for managing a presamples package. Packages are directories, stored either locally or on a network resource (via `PyFilesystem <https://www.pyfilesystem.org/>`__.

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

    @property
    def metadata(self):
        return json.load(open(self.path / "datapackage.json"))

    @property
    def name(self):
        return self.metadata['name']

    @property
    def seed(self):
        return self.metadata['seed']

    def change_seed(self, new):
        """Change seed to ``new``"""
        current = json.load(open())
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
            self._parameters = ParametersNestedMapping(self)
        return self._parameters


class ParametersNestedMapping(Mapping):
    def __init__(self, package):
        self.package = package
        self.data = {r['label']: self.load_resource(r) for r in self.resources}

    def load_resource(self, obj):
        maybe_float = lambda x: float(x) if x.shape in ((), (1,)) else x

        names = json.load(open(os.path.join(self.path, obj['names']['filepath'])))
        samples = np.load(os.path.join(self.path, obj['samples']['filepath']))
        return {x: maybe_float(y.ravel()) for x, y in zip(names, samples)}

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return len(self.data)

    def __contains__(self, k):
        return k in self.data

    def __iter__(self):
        return iter(self.data)

    @property
    def name_conflicts(self):
        return sum(len(o) for o in self.values()) != len({x for v in self.values() for x in v})

    def flattened(self):
        if self.name_conflicts:
            raise NameConflicts

        return {y: z for x in self.values() for y, z in x.items()}
