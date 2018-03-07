from .errors import NameConflicts
from bw2calc.utils import md5
from pathlib import Path
import json
import numpy as np
import os


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
        open(path / "datapackage.json"),
        encoding="utf-8"
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
