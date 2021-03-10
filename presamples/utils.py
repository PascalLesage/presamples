from .errors import NameConflicts
from pathlib import Path
import hashlib
import json
import numpy as np
import os


def md5(filepath, blocksize=65536):
    """Generate MD5 hash for file at `filepath`"""
    hasher = hashlib.md5()
    fo = open(filepath, 'rb')
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()


def convert_parameter_dict_to_presamples(parameters):
    """Convert a dictionary of named parameters to the form needed for ``parameter_presamples``.

    ``parameters`` should be a dictionary with names (as strings) as keys and Numpy arrays as values. All Numpy arrays should have the same shape.

    Returns (numpy samples array, list of names).

    """
    names = sorted(parameters.keys())
    shapes = {obj.shape for obj in parameters.values()}
    if len(shapes) != 1:
        raise ValueError(
            "Hetergeneous array shapes ({}) not allowed".format(shapes)
        )
    return names, np.vstack([parameters[key].reshape((1, -1)) for key in names])


def validate_presamples_dirpath(path):
    """Check that a ``dirpath`` has a valid `datapackage.json` file and data files with matching hashes."""
    path = Path(path)
    assert os.path.isdir(path)
    files = list(os.listdir(path))
    assert "datapackage.json" in files, "{} missing a datapackage file".format(path)
    metadata = json.load(
        open(path / "datapackage.json")
    )
    for resource in metadata['resources']:
        assert os.path.isfile(path / resource['samples']['filepath'])
        assert md5(path / resource['samples']['filepath']) == \
            resource['samples']['md5']
        if 'indices' in resource:
            assert os.path.isfile(path / resource['indices']['filepath'])
            assert md5(path / resource['indices']['filepath']) == \
                resource['indices']['md5']
        if 'names' in resource:
            assert os.path.isfile(path / resource['names']['filepath'])
            assert md5(path / resource['names']['filepath']) == \
                resource['names']['md5']


def check_name_conflicts(lists):
    """Check if there are overlapping names in ``lists``.

    Each element of ``lists`` is an iterable of parameter names."""
    names = [name for lst in lists for name in lst]
    if len(set(names)) != len(names):
        raise NameConflicts

def change_resource_path(resource, new_path_parent):
    """Change the path of a resource to new_path

    Does *not* actually move the presamples package, but simply changes the path
    """
    old_path = Path(resource.path)
    new_path_parent = Path(new_path_parent)
    resource.path = new_path_parent / old_path.name
    resource.save()
