from bw2calc.utils import md5
from pathlib import Path
import json
import numpy as np
import os


class PackageBase:
    """Base class for presample packages.

    Provides methods common to all presample package classes."""
    def validate_dirpath(self, path):
        """Check that a ``dirpath`` has a valid `datapackage.json` file and data files with matching hashes."""
        assert os.path.isdir(path)
        files = list(os.listdir(path))
        assert "datapackage.json" in files, "{} missing a datapackage file".format(path)
        metadata = json.load(
            open(path / "datapackage.json"),
            encoding="utf-8"
        )
        for resource in metadata['resources']:
            assert os.path.isfile(path / resource['samples']['filepath'])
            assert md5(path / resource['samples']['filepath']) == \
                resource['samples']['md5']
            assert os.path.isfile(path / resource['indices']['filepath'])
            assert md5(path / resource['indices']['filepath']) == \
                resource['indices']['md5']

    def __init__(self, path):
        self.path = Path(path)
        self.validate_dirpath(self.path)

    @property
    def metadata(self):
        return json.load(open(self.path / "datapackage.json"))

    @property
    def name(self):
        return self.metadata['name']

    @property
    def id(self):
        return self.metadata['id']

    @property
    def resources(self):
        return self.metadata['resources']


class PresamplesPackage(PackageBase):
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
    @property
    def matrix_presamples(self):
        return
        # for obj in self.resources:
        #     if 'matrix'
