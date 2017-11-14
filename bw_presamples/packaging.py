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


def split_inventory_presamples(samples, indices):
    pass


def format_technosphere_presamples(indices):
    """Format technosphere presamples into an array.

    Input data has the form ``[(input id, output id, type)]``. Both the input and output ids should **not** be mapped already; the ``type`` may be mapped or not.

    Returns an array with columns ``[('input', np.uint32), ('output', np.uint32), ('row', MAX_SIGNED_32BIT_INT), ('col', MAX_SIGNED_32BIT_INT), ('type', np.uint8)]``, and the following metadata::

        {
            'row from label': 'input',
            'row to label': 'row',
            'row dict': 'product_dict',
            'col from label': 'output',
            'col to label': 'col',
            'col dict': 'activity_dict',
            'matrix': 'technosphere_matrix'
        }

    """
    metadata = {
        'row from label': 'input',
        'row to label': 'row',
        'row dict': 'product_dict',
        'col from label': 'output',
        'col to label': 'col',
        'col dict': 'activity_dict',
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
            mapping[row[0]],
            mapping[row[1]],
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
            'row dict': 'biosphere_dict',
            'col from label': 'output',
            'col to label': 'col',
            'col dict': 'activity_dict',
            'matrix': 'biosphere_matrix'
        }

    """
    metadata = {
        'row from label': 'input',
        'row to label': 'row',
        'row dict': 'biosphere_dict',
        'col from label': 'output',
        'col to label': 'col',
        'col dict': 'activity_dict',
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
            mapping[row[0]],
            mapping[row[1]],
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
            'row dict': 'biosphere_dict',
            'matrix': 'characterization_matrix'
        }

    """
    metadata =         {
        'row from label': 'flow',
        'row to label': 'row',
        'row dict': 'biosphere_dict',
        'matrix': 'characterization_matrix'
    }
    dtype = [
        ('flow', np.uint32),
        ('row', np.uint32),
    ]
    func = lambda row: (mapping[row], MAX_SIGNED_32BIT_INT)
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


def create_matrix_presamples_package(data, name=None,
        id_=None, overwrite=False):
    """Create a new subdirectory in the ``project`` folder that stores presampled values.

    The following arguments are optional:
    * ``id_``: Unique id for this collection of presamples. Optional, generated automatically if not set.
    * ``overwrite``: If True, replace an existing presamples package with the same ``_id`` if it exists. Default ``False``

    Returns ``id_`` and the absolute path of the created directory.

    """
    # Convert all arrays
    to_array = lambda x: np.array(x) if not isinstance(x, np.ndarray) else x
    to_2d = lambda x: np.reshape(x, (1, -1)) if len(x.shape) == 1 else x
    id_ = id_ or uuid.uuid4().hex

    # Create presamples directory
    dirpath = Path(projects.request_directory('presamples')) / id_
    if os.path.isdir(dirpath):
        if not overwrite:
            raise ValueError("The presampled directory {} already exists".format(dirpath))
        else:
            shutil.rmtree(dirpath)
    os.mkdir(dirpath)

    datapackage = {
        "name": str(name),
        "id": id_,
        "profile": "data-package",
        "resources": []
    }

    for index, row in enumerate(data):
        samples, indices, kind, *other = row
        samples = to_2d(to_array(samples))
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
                'dtype': str(samples.dtype)
            },
            'indices': {
                'filepath': indices_fp,
                'md5': md5(dirpath / indices_fp),
            },
            "profile": "data-resource",
            "format": "npy",
            "mediatype": "application/octet-stream"
        }
        result.update(metadata)
        datapackage['resources'].append(result)

    with open(dirpath / "datapackage.json", "w", encoding='utf-8') as f:
        json.dump(datapackage, f, indent=2, ensure_ascii=False)

    return id_, dirpath



    # if parameters is not None:
    #     assert parameters_samples is not None, "Exogenous parameters were passed, but parameter samples are missing."
    #     assert len(parameters)==parameters_samples.shape[0], "The number of exogenous parameters ({}) does not correspond to the number of samples {}".format(len(parameters), parameters_samples.shape[0])

    #     parameters_samples_fp = os.path.join(base_dir, "{}.parameters_samples.npy".format(id_))
    #     parameters_fp = os.path.join(base_dir, "{}.parameters.json".format(id_))

    #     with open(parameters_fp, "w") as f:
    #         json.dump(parameters, f)
    #     np.save(parameters_samples_fp, parameters_samples, allow_pickle=False)

    #     datapackage['content'].append('parameters')
    #     datapackage['resources'].extend(
    #         [
    #         {
    #             "name": "parameters_samples",
    #             "path": "{}.parameters_samples.npy".format(id_),
    #             "profile": "data-resource",
    #             "format": "npy",
    #             "mediatype": "application/octet-stream",
    #             "hash": md5(parameters_samples_fp),
    #             "dtype": parameters_dtype,
    #             "shape": parameters_samples.shape
    #         }, {
    #             "name": "parameters",
    #             "path": "{}.parameters.json".format(id_),
    #             "profile": "data-resource",
    #             "format": "json",
    #             "mediatype": "application/json",
    #             "hash": md5(parameters_fp),
    #         }
    #         ])


# def convert_parameter_set_dict_to_presample_package(ps_dict, id_=None,
#                                                     overwrite=None,
#                                                     forced_precision="float32"
#                                                     ):
#     if ps_dict.get('parameters'):
#         parameters = ps_dict['parameters']
#         parameters_samples = ps_dict['parameters_samples']
#     else:
#         parameters = None
#         parameters_samples = None

#     if ps_dict.get('inventory_elements'):
#         inventory_elements = ps_dict['inventory_elements']
#         inventory_elements_samples = ps_dict['inventory_elements_samples']
#     else:
#         inventory_elements = None
#         inventory_elements_samples = None

#     if ps_dict.get('cfs'):
#         inventory_elements = ps_dict['cfs']
#         inventory_elements_samples = ps_dict['cfs_samples']
#     else:
#         cfs = None
#         cfs_samples = None

#     id_, base_dir = create_presamples_package(inventory_elements=inventory_elements,
#         inventory_elements_samples=inventory_elements_samples, inventory_dtype=forced_precision,
#         cfs=cfs, cfs_samples=cfs_samples, cfs_dtype=forced_precision,
#         parameters=parameters, parameters_samples=parameters_samples, parameters_dtype=forced_precision,
#         id_=id_, overwrite=overwrite
#         )
#     return id_, base_dir
