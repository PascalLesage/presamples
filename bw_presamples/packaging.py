from bw2data import projects, mapping
from bw2data.filesystem import md5
from bw2data.utils import TYPE_DICTIONARY
from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import os
import shutil
import uuid


# Max signed 32 bit integer, compatible with Windows
MAX_SIGNED_32BIT_INT = 2147483647

to_array = lambda x: np.array(x) if not isinstance(x, np.ndarray) else x
to_2d = lambda x: np.reshape(x, (1, -1)) if len(x.shape) == 1 else x


def split_inventory_presamples(samples, indices):
    """Split technosphere and biosphere presamples.

    ``samples`` is a Numpy array with rows of exchanges and columns of Monte Carlo iterations. ``indices`` is a list of ``[(input key, output key, type)]``, where ``type`` is like "biosphere" or "technosphere". Everything which isn't type ``biosphere`` will be added to the technosphere presamples.

    Returns ((biosphere samples, biosphere indices, label), (technosphere samples, technosphere indices, label)).

    # TODO: But only if they both exist

    """
    assert isinstance(samples, np.ndarray)
    assert samples.shape[0] == len(indices), "Shape mismatch"

    mask = np.array([o[2] == 'biosphere' for o in indices])
    no_empty = lambda lst: [o for o in lst if o[1]]

    return no_empty([
        (samples[mask, :], [o[:2] for o in indices if o[2] == "biosphere"], "biosphere"),
        (samples[~mask, :], [o for o in indices if o[2] != "biosphere"], "technosphere"),
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
    return format_matrix_presamples(indices, 'technosphere', dtype, func, metadata)


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
    return format_matrix_presamples(indices, 'biosphere', dtype, func, metadata)


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
    return format_matrix_presamples(indices, 'cf', dtype, func, metadata)


FORMATTERS = {
    'technosphere': format_technosphere_presamples,
    'biosphere': format_biosphere_presamples,
    'cf': format_cf_presamples,
}


def validate_matrix_presamples_metadata(metadata, dtype):
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


def format_matrix_presamples(indices, kind, dtype=None, row_formatter=None, metadata=None):
    if dtype is None and row_formatter is None and metadata is None:
        try:
            return FORMATTERS[kind](indices)
        except KeyError:
            raise KeyError("Can't find formatter for {}".format(kind))
    elif dtype is None or row_formatter is None or metadata is None:
        raise ValueError("Must provide ``dtype``, ``row_formatter``, and ``metadata``")
    else:
        validate_matrix_presamples_metadata(metadata, dtype)

        array = np.zeros(len(indices), dtype=dtype)
        for index, row in enumerate(indices):
            array[index] = row_formatter(row)

        return array, metadata


def get_presample_directory(id_, overwrite=False, dirpath=None):
    if dirpath is None:
        dirpath = Path(projects.request_directory('presamples')) / id_
    else:
        dirpath = Path(dirpath) / id_
    if os.path.isdir(dirpath):
        if not overwrite:
            raise ValueError("The presampled directory {} already exists".format(dirpath))
        else:
            shutil.rmtree(dirpath)
    os.mkdir(dirpath)
    return dirpath


def create_presamples_package(matrix_presamples=None, parameter_presamples=None, name=None,
        id_=None, overwrite=False, dirpath=None):
    """Create and populate a new presamples directory that stores presampled values for matrix data and/or named parameters.

    ``matrix_presamples`` is a list of :ref:`matrix-presamples`; parameter_presamples`` is a list of :ref:`parameter-presamples`. Both are allowed, but at least one type of presamples must be given. The documentation gives more details on these input arguments.

    Both matrix and parameter data should have the same number of possible values (i.e same number of Monte Carlo iterations).

    The following arguments are optional:
    * ``name``: A human-readable name for these samples.
    * ``id_``: Unique id for this collection of presamples. Optional, generated automatically if not set.
    * ``overwrite``: If True, replace an existing presamples package with the same ``_id`` if it exists. Default ``False``
    * ``dirpath``: An optional directory path where presamples can be created. Default is to create a subdirectory in the ``project`` folder.

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
        "resources": []
    }

    if not matrix_presamples and not parameter_presamples:
        raise ValueError("Must specify at least one of `matrix_presamples` and `parameter_presamples`")

    index = 0

    def elems(lst, label):
        """Yield elements from ``lst``. If an element is a model instance, iterate over its components."""
        for elem in lst:
            if hasattr(elem, label):
                for obj in getattr(elem, label):
                    yield obj
            else:
                yield elem

    for index, row in enumerate(elems(matrix_presamples or [], "matrix_presamples")):
        samples, indices, kind, *other = row
        samples = to_2d(to_array(samples))

        if num_iterations is None:
            num_iterations = samples.shape[1]
        if samples.shape[1] != num_iterations:
            raise ValueError("Inconsistent number of Monte Carlo iterations: "
                "{} and {}".format(samples.shape[1], num_iterations))

        indices, metadata = format_matrix_presamples(indices, kind, *other)

        if samples.shape[0] != indices.shape[0]:
            error = "Shape mismatch between samples and indices: {}, {}, {}"
            raise ValueError(error.format(samples.shape, indices.shape, kind))

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
            'indices': {
                'filepath': indices_fp,
                'md5': md5(dirpath / indices_fp),
                "format": "npy",
                "mediatype": "application/octet-stream",
            },
            "profile": "data-resource",
        }
        result.update(metadata)
        datapackage['resources'].append(result)

    offset = index + (1 if index else 0)
    for index, row in enumerate(elems(parameter_presamples or [], "parameter_presamples")):
        samples, names = row
        samples = to_2d(to_array(samples))

        if num_iterations is None:
            num_iterations = samples.shape[1]
        if samples.shape[1] != num_iterations:
            raise ValueError("Inconsistent number of Monte Carlo iterations: "
                "{} and {}".format(samples.shape[1], num_iterations))

        if not len(names) == samples.shape[0]:
            raise ValueError("Shape mismatch between samples and names: "
                "{}, {}".format(samples.shape, len(names)))

        samples_fp = "{}.{}.samples.npy".format(id_, offset + index)
        names_fp = "{}.{}.names.json".format(id_, offset + index)

        np.save(dirpath / samples_fp, samples, allow_pickle=False)
        with open(dirpath / names_fp, "w", encoding='utf-8') as f:
            json.dump(names, f, ensure_ascii=False)

        result = {
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
        }
        datapackage['resources'].append(result)

    with open(dirpath / "datapackage.json", "w", encoding='utf-8') as f:
        json.dump(datapackage, f, indent=2, ensure_ascii=False)

    return id_, dirpath
