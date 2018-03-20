from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import os
import shutil
import uuid

from bw2calc.utils import md5
from .errors import InconsistentSampleNumber, ShapeMismatch, NameConflicts
from .utils import validate_presamples_dirpath

try:
    from bw2data.utils import TYPE_DICTIONARY
    from bw2data import projects, mapping
except ImportError:
    TYPE_DICTIONARY = {
        "unknown": -1,
        "production": 0,
        "technosphere": 1,
        "biosphere": 2,
        "substitution": 3,
    }
    projects = None
    mapping = {}

# Max signed 32 bit integer, compatible with Windows
MAX_SIGNED_32BIT_INT = 2147483647

to_array = lambda x: np.array(x) if not isinstance(x, np.ndarray) else x
to_2d = lambda x: np.reshape(x, (1, -1)) if len(x.shape) == 1 else x


def split_inventory_presamples(samples, indices):
    """Split technosphere and biosphere presamples.

    ``samples`` is a Numpy array with rows of exchanges and columns of samples. ``indices`` is a list of ``[(input key, output key, type)]``, where ``type`` is like "biosphere" or "technosphere". Everything which isn't type ``biosphere`` will be added to the technosphere presamples.

    Returns a list of ((biosphere samples, biosphere indices, label), (technosphere samples, technosphere indices, label)) - but will skip either element if there are no samples.

    """
    assert isinstance(samples, np.ndarray)
    if samples.shape[0] != len(indices):
        raise ShapeMismatch("Shape mismatch: {}, {}".format(samples.shape[0], len(indices)))

    mask = np.array([o[2] in (2, 'biosphere') for o in indices])
    no_empty = lambda lst: [o for o in lst if o[1]]

    return no_empty([
        (
            samples[mask, :],
            [o[:2] for o in indices if o[2] in (2, "biosphere")],
            "biosphere"
        ), (
            samples[~mask, :],
            [o for o in indices if o[2] not in (2, "biosphere")],
            "technosphere"
        ),
    ])


def format_technosphere_presamples(indices):
    """Format technosphere presamples into an array.

    Input data has the form ``[(input id, output id, type)]``. Both the input and output ids can be mapped already, but normally aren't; the ``type`` may be mapped or not.

    Returns an array with columns ``[('input', np.uint32), ('output', np.uint32), ('row', MAX_SIGNED_32BIT_INT), ('col', MAX_SIGNED_32BIT_INT), ('type', np.uint8)]``, and the following metadata::

        {
            'row from label': 'input',
            'row to label': 'row',
            'row dict': '_product_dict',
            'col from label': 'output',
            'col to label': 'col',
            'col dict': '_activity_dict',
            'matrix': 'technosphere_matrix'
        }

    """
    metadata = {
        'row from label': 'input',
        'row to label': 'row',
        'row dict': '_product_dict',
        'col from label': 'output',
        'col to label': 'col',
        'col dict': '_activity_dict',
        'matrix': 'technosphere_matrix'
    }
    dtype = [
        ('input', np.uint32),
        ('output', np.uint32),
        ('row', np.uint32),
        ('col', np.uint32),
        ('type', np.uint8),
    ]
    def func(row):
        return (
            mapping.get(row[0], row[0]),
            mapping.get(row[1], row[1]),
            MAX_SIGNED_32BIT_INT,
            MAX_SIGNED_32BIT_INT,
            TYPE_DICTIONARY.get(row[2], row[2])
        )
    return format_matrix_data(indices, 'technosphere', dtype, func, metadata)


def format_biosphere_presamples(indices):
    """Format biosphere presamples into an array.

    Input data has the form ``[(flow id, activity id)]``, where both ids are **unmapped**.

    Returns an array with columns ``[('input', np.uint32), ('output', np.uint32), ('row', MAX_SIGNED_32BIT_INT), ('col', MAX_SIGNED_32BIT_INT)]``, and the following metadata::

        {
            'row from label': 'input',
            'row to label': 'row',
            'row dict': '_biosphere_dict',
            'col from label': 'output',
            'col to label': 'col',
            'col dict': '_activity_dict',
            'matrix': 'biosphere_matrix'
        }

    """
    metadata = {
        'row from label': 'input',
        'row to label': 'row',
        'row dict': '_biosphere_dict',
        'col from label': 'output',
        'col to label': 'col',
        'col dict': '_activity_dict',
        'matrix': 'biosphere_matrix'
    }
    dtype = [
        ('input', np.uint32),
        ('output', np.uint32),
        ('row', np.uint32),
        ('col', np.uint32),
    ]
    def func(row):
        return (
            mapping.get(row[0], row[0]),
            mapping.get(row[1], row[0]),
            MAX_SIGNED_32BIT_INT,
            MAX_SIGNED_32BIT_INT,
        )
    return format_matrix_data(indices, 'biosphere', dtype, func, metadata)


def format_cf_presamples(indices):
    """Format characterization factor presamples into an array.

    Input data has the form ``[flow id]``, where ``flow id`` is an **unmapped** biosphere flow key like ``('biosphere', 'something')``.

    Returns an array with columns ``[('flow', np.uint32), ('row', MAX_SIGNED_32BIT_INT)]``, and the following metadata::

        {
            'row from label': 'flow',
            'row to label': 'row',
            'row dict': '_biosphere_dict',
            'matrix': 'characterization_matrix'
        }

    """
    metadata =         {
        'row from label': 'flow',
        'row to label': 'row',
        'row dict': '_biosphere_dict',
        'matrix': 'characterization_matrix'
    }
    dtype = [
        ('flow', np.uint32),
        ('row', np.uint32),
    ]
    func = lambda row: (mapping.get(row, row), MAX_SIGNED_32BIT_INT)
    return format_matrix_data(indices, 'cf', dtype, func, metadata)


FORMATTERS = {
    'technosphere': format_technosphere_presamples,
    'biosphere': format_biosphere_presamples,
    'cf': format_cf_presamples,
}


def validate_matrix_data_metadata(metadata, dtype):
    """Make sure ``metdata`` has the required keys, and that ``indices`` agress with ``metadata``."""
    ROWS = ('row from label', 'row to label', 'row dict', 'matrix')
    COLUMNS = ('col from label', 'col to label', 'col dict')
    if not all(field in metadata for field in ROWS):
        raise ValueError("Must give each of {}".format(ROWS))
    if "col dict" in metadata and not \
            all(field in metadata for field in COLUMNS):
        raise ValueError("Must give each of {}".format(COLUMNS))
    col_names = {x[0] for x in dtype}
    metadata_names = {v for k, v in metadata.items() if "label" in k}
    missing = metadata_names.difference(col_names)
    if missing:
        raise ValueError("The following necessary columns are not in the "
            "indices: {}".format(missing))


def format_matrix_data(indices, kind, dtype=None, row_formatter=None, metadata=None):
    if dtype is None and row_formatter is None and metadata is None:
        try:
            return FORMATTERS[kind](indices)
        except KeyError:
            raise KeyError("Can't find formatter for {}".format(kind))
    elif dtype is None or row_formatter is None or metadata is None:
        raise ValueError("Must provide ``dtype``, ``row_formatter``, and ``metadata``")
    else:
        validate_matrix_data_metadata(metadata, dtype)

        array = np.zeros(len(indices), dtype=dtype)
        for index, row in enumerate(indices):
            array[index] = row_formatter(row)

        return array, metadata


def get_presample_directory(id_, overwrite=False, dirpath=None):
    if dirpath is None:
        if projects:
            dirpath = Path(projects.request_directory('presamples')) / id_
        else:
            dirpath = Path(os.getcwd()) / id_
    else:
        dirpath = Path(dirpath) / id_
    if os.path.isdir(dirpath):
        if not overwrite:
            raise ValueError("The presampled directory {} already exists".format(dirpath))
        else:
            shutil.rmtree(dirpath)
    os.mkdir(dirpath)
    return dirpath


def create_presamples_package(matrix_data=None, parameter_data=None, name=None,
        id_=None, overwrite=False, dirpath=None, seed=None):
    """Create and populate a new presamples directory that stores presampled values for matrix data and/or named parameters.

    ``matrix_data`` is a list of :ref:`matrix-presamples`; parameter_data`` is a list of :ref:`parameter-presamples`. Both are allowed, but at least one type of presamples must be given. The documentation gives more details on these input arguments.

    Both matrix and parameter data should have the same number of possible values (i.e same number of samples).

    The following arguments are optional:
    * ``name``: A human-readable name for these samples.
    * ``id_``: Unique id for this collection of presamples. Optional, generated automatically if not set.
    * ``overwrite``: If True, replace an existing presamples package with the same ``_id`` if it exists. Default ``False``
    * ``dirpath``: An optional directory path where presamples can be created. Default is to create a subdirectory in the ``project`` folder.
    * ``seed``: Seed used by indexer to return array columns in random order. Can be an integer, "sequential" or None.

    Returns ``id_`` and the absolute path of the created directory.

    """
    id_ = id_ or uuid.uuid4().hex
    name = name or id_

    if dirpath is not None:
        assert os.path.isdir(dirpath), "`dirpath` must be a directory"
        assert os.access(dirpath, os.W_OK), "`dirpath` must be a writable directory"
        dirpath = os.path.abspath(dirpath)
    dirpath = get_presample_directory(id_, overwrite, dirpath=dirpath)

    num_iterations = None
    datapackage = {
        "name": str(name),
        "id": id_,
        "profile": "data-package",
        "seed": seed,
        "resources": []
    }

    if not matrix_data and not parameter_data:
        raise ValueError("Must specify at least one of `matrix_data` and `parameter_data`")

    def elems(lst, label):
        """Yield elements from ``lst``. If an element is a model instance, iterate over its components."""
        for elem in lst:
            if hasattr(elem, label):
                for obj in getattr(elem, label):
                    yield obj
            else:
                yield elem

    # Not defined if matrix_data is empty
    index = -1
    for index, row in enumerate(elems(matrix_data or [], "matrix_data")):
        samples, indices, kind, *other = row
        samples = to_2d(to_array(samples))

        if num_iterations is None:
            num_iterations = samples.shape[1]
        if samples.shape[1] != num_iterations:
            raise InconsistentSampleNumber("Inconsistent number of samples: "
                "{} and {}".format(samples.shape[1], num_iterations))

        indices, metadata = format_matrix_data(indices, kind, *other)

        if samples.shape[0] != indices.shape[0]:
            error = "Shape mismatch between samples and indices: {}, {}, {}"
            raise ShapeMismatch(error.format(samples.shape, indices.shape, kind))

        result = write_matrix_data(samples, indices, metadata, kind, dirpath, index, id_)
        datapackage['resources'].append(result)

    names = [
        name for _, names, _ in elems(parameter_data or [], "parameter_data")
        for name in names
    ]

    num_names = len(names)
    num_unique_names = len(set(names))
    if num_names != num_unique_names:
        raise NameConflicts(
            "{} named parameters, but only {} unique names".format(
            num_names, num_unique_names
        ))

    offset = (index + 1) if index != -1 else 0
    for index, row in enumerate(elems(parameter_data or [], "parameter_data")):
        samples, names, label = row

        samples = to_2d(to_array(samples))
        if not len(names) == samples.shape[0]:
            raise ShapeMismatch("Shape mismatch between samples and names: "
                "{}, {}".format(samples.shape, len(names)))

        if num_iterations is None:
            num_iterations = samples.shape[1]
        if samples.shape[1] != num_iterations:
            raise InconsistentSampleNumber("Inconsistent number of samples: "
                "{} and {}".format(samples.shape[1], num_iterations))

        result = write_parameter_data(samples, names, label, dirpath,
                                            offset + index, id_)
        datapackage['resources'].append(result)

    datapackage['ncols'] = num_iterations

    with open(dirpath / "datapackage.json", "w", encoding='utf-8') as f:
        json.dump(datapackage, f, indent=2, ensure_ascii=False)

    return id_, dirpath


def append_presamples_package(dirpath, matrix_data=None, parameter_data=None):
    """Append new sections to a presamples package.

    ``dirpath`` is the directory where the existing presamples can be found.

    ``matrix_data`` is a list of :ref:`matrix-presamples`; parameter_data`` is a list of :ref:`parameter-presamples`. Both are allowed, but at least one type of presamples must be given. The documentation gives more details on these input arguments.

    Both matrix and parameter data should have the same number of possible values (i.e same number of samples).

    The following arguments are optional:

    Returns the absolute path of the presamples directory.

    """
    dirpath = Path(dirpath)
    validate_presamples_dirpath(dirpath)

    datapackage = json.load(open(dirpath / "datapackage.json"))
    num_iterations = datapackage['ncols']

    if not matrix_data and not parameter_data:
        raise ValueError("Must specify at least one of `matrix_data` and `parameter_data`")

    offset = max(o['index'] for o in datapackage['resources']) + 1

    def elems(lst, label):
        """Yield elements from ``lst``. If an element is a model instance, iterate over its components."""
        for elem in lst:
            if hasattr(elem, label):
                for obj in getattr(elem, label):
                    yield obj
            else:
                yield elem

    # Not defined if matrix_data is empty
    index = -1
    for index, row in enumerate(elems(matrix_data or [], "matrix_data")):
        samples, indices, kind, *other = row
        samples = to_2d(to_array(samples))

        if samples.shape[1] != num_iterations:
            raise InconsistentSampleNumber("Inconsistent number of samples: "
                "{} and {}".format(samples.shape[1], num_iterations))

        indices, metadata = format_matrix_data(indices, kind, *other)

        if samples.shape[0] != indices.shape[0]:
            error = "Shape mismatch between samples and indices: {}, {}, {}"
            raise ShapeMismatch(error.format(samples.shape, indices.shape, kind))

        result = write_matrix_data(
            samples, indices, metadata, kind,
            dirpath, index + offset, datapackage['id']
        )
        datapackage['resources'].append(result)

    if parameter_data:
        filepaths = [dirpath / resource['names']['filepath'] for resource in datapackage['resources'] if 'names' in resource]
        old_names = [name for fp in filepaths for name in json.load(open(fp))]
        names = [
            name for _, names, _ in elems(parameter_data or [], "parameter_data")
            for name in names
        ]
        print(old_names)
        print(names)
        if set(old_names).intersection(set(names)):
            raise NameConflicts(
                "Named parameters already defined in existing package: {}".format(
                set(old_names).intersection(set(names))
            ))

        num_names = len(names)
        num_unique_names = len(set(names))
        if num_names != num_unique_names:
            raise NameConflicts(
                "{} named parameters, but only {} unique names".format(
                num_names, num_unique_names
            ))

    offset += (index + 1) if index != -1 else 0
    for index, row in enumerate(elems(parameter_data or [], "parameter_data")):
        samples, names, label = row

        if samples.shape[1] != num_iterations:
            raise InconsistentSampleNumber("Inconsistent number of samples: "
                "{} and {}".format(samples.shape[1], num_iterations))

        result = write_parameter_data(
            samples, names, label, dirpath,
            offset + index, datapackage['id']
        )
        datapackage['resources'].append(result)

    with open(dirpath / "datapackage.json", "w", encoding='utf-8') as f:
        json.dump(datapackage, f, indent=2, ensure_ascii=False)

    return datapackage['id'], dirpath


def write_matrix_data(samples, indices, metadata, kind, dirpath, index, id_):
    samples_fp = "{}.{}.samples.npy".format(id_, index)
    indices_fp = "{}.{}.indices.npy".format(id_, index)
    np.save(dirpath / samples_fp, samples, allow_pickle=False)
    np.save(dirpath / indices_fp, indices, allow_pickle=False)

    result = {
        'type': kind,
        'samples': {
            'filepath': samples_fp,
            'md5': md5(dirpath / samples_fp),
            'shape': samples.shape,
            'dtype': str(samples.dtype),
            "format": "npy",
            "mediatype": "application/octet-stream",
        },
        'index': index,
        'indices': {
            'filepath': indices_fp,
            'md5': md5(dirpath / indices_fp),
            "format": "npy",
            "mediatype": "application/octet-stream",
        },
        "profile": "data-resource",
    }
    result.update(metadata)
    return result


def write_parameter_data(samples, names, label, dirpath, index, id_):
    samples_fp = "{}.{}.samples.npy".format(id_, index)
    names_fp = "{}.{}.names.json".format(id_, index)

    np.save(dirpath / samples_fp, samples, allow_pickle=False)
    with open(dirpath / names_fp, "w", encoding='utf-8') as f:
        json.dump(names, f, ensure_ascii=False)

    return {
        'samples': {
            'filepath': samples_fp,
            'md5': md5(dirpath / samples_fp),
            'shape': samples.shape,
            'dtype': str(samples.dtype),
            "format": "npy",
            "mediatype": "application/octet-stream"
        },
        'names': {
            'filepath': names_fp,
            'md5': md5(dirpath / names_fp),
            "format": "json",
            "mediatype": "application/json"
        },
        "profile": "data-resource",
        "label": label,
        'index': index,
    }
