from __future__ import print_function, unicode_literals
from eight import *

from bw2data import projects,mapping
from bw2data.filesystem import md5
from bw2data.utils import MAX_INT_32, TYPE_DICTIONARY, numpy_string
import json
import numpy as np
import os
import shutil
import uuid

def convert_1d_to_2d_if_needed(arr):
    """Convert, if applicable, a 1d numpy array to a 2d numpy array"""
    if arr is not None and len(arr.shape)==1:
        return np.reshape(arr, (1, arr.shape[0]))
    else:
        return arr

def create_presamples_package(inventory_elements=None, inventory_elements_samples=None, inventory_mapped=False, inventory_dtype="float32",
                              cfs=None, cfs_samples=None, cfs_mapped=False, cfs_dtype="float32",
                              parameters=None, parameters_samples=None, parameters_dtype="float32",
                              id_=None, overwrite=False, description="", name=None):
    """Create a new subdirectory in the ``project`` folder that stores presampled values.

    The presamples values can be for the following types of objects:
        * Elements of the inventory matrices (A or B matrices)
        * Characterization factors (i.e. elements of the C matrix)
        * Exogenous parameters
    
    The presamples directory necessarily contains the following file:
    * ``datapackage.json``: Contains metadata about the other files, including integrity checks. 
    
    If the presamples package is to contain sampled values for elements of the inventory matrices,
    the presamples directory necessarily holds the following two additional files:
    * ``{id_}.inventory_elements.npy``: Information to locate the presampled values in the A and B matrices.
    * ``{id_}.inventory_elements_samples.npy``: Array of the presampled values for the corresponding inventory elements.
    
    If the presamples package is to contain sampled values for characterization factors,
    the presamples directory necessarily holds the following two additional files:
    * ``{id_}.cfs.npy``: Information to locate the presampled values in the C matrix.
    * ``{id_}.cfs_samples.npy``: Array of the presampled values for the corresponding characterization factors

    If the presamples package is to contain sampled values for exogenous parameters,
    the presamples directory necessarily holds the following two additional files:
    * ``{id_}.parameters.json``: List of exogenous parameters.
    * ``{id_}.parameters_samples.npy``: Array of the presampled values for exogenous parameters.

    The arguments that are passed depend on the type of values the presamples package should hold. 

    If the presamples package is to contain sampled values for elements of the A or B matrices,
    the following arguments are obligatory:
    * ``inventory_elements``: 
            The format is (input activity, output activity, string label for exchange type), 
            e.g. ``[("my database", "an input"), ("my database", "an output"), "technosphere"]``.
    * ``elements_samples``:
            Array with sampled values for the elements. Columns represent dependent iterations,
            each row relates to the corresponding row in ``inventory_elements``
    * ``inventory_mapped``: Are the arrays in ``inventory_elements`` already mapped to integers using ``mapping``. Boolean, default ``False``.
    
    If the presamples package is to contain sampled values for characterization factors,
    the following arguments are obligatory:
    * ``cfs``: 
            The format is a list of flow identifiers, e.g. ``[('biosphere3', 'f9055607-c571-4903-85a8-7c20e3790c43')]``.
    * ``cfs_samples``:
            Array with sampled values for the elements. Columns represent dependent iterations,
            each row relates to the corresponding row in ``cfs``
    * ``cfs_mapped``: Are the arrays in ``cfs`` already mapped to integers using ``mapping``. Boolean, default ``False``.

    If the presamples package is to contain sampled values for exogenous parameters,
    the following arguments are obligatory:
    * ``parameters``: A list containing information on exogenous parameters
    * ``parameters_samples``: Array with sampled values for exogenous parameters
    
    The following arguments are optional:
    * ``id_``: Unique id for this collection of presamples. Optional, generated automatically if not set.
    * ``overwrite``: If True, replace an existing presamples package with the same ``_id`` if it exists. Default ``False``
    * ``description``: Markdown description of the presamples package content and context
    * ``name``: short url-usable (and preferably human-readable) name of the package. If ``None``, the ``name`` is set equal to ``_id``

    Returns ``id_`` and the absolute path of the created directory.

    """

    # Convert all samples_arrays to 2d, if necessary:
    inventory_elements_samples = convert_1d_to_2d_if_needed(inventory_elements_samples)
    cfs_samples = convert_1d_to_2d_if_needed(cfs_samples)
    parameters_samples = convert_1d_to_2d_if_needed(parameters_samples) 
    
    # Ensure all samples are numpy arrays with the same number of iterations
    passed_samples = [samples for samples in [inventory_elements_samples, cfs_samples, parameters_samples] if samples is not None]
    assert all([isinstance(arr, (np.ndarray, None)) for arr in passed_samples]), "Not all passed samples are numpy arrays"
    if len(passed_samples)>1:
        assert all([arr.shape[1] == passed_samples[0].shape[1] for arr in passed_samples]), "The number of iterations in passed samples are not constant across types of samples"

    # Generate id_ 
    if id_ is None:
        id_ = uuid.uuid4().hex
    if name in None:
        name = id_
    
    # Create presamples directory
    base_dir = os.path.join(projects.request_directory('presamples'), id_)
    if os.path.isdir(base_dir):
        if not overwrite:
            raise ValueError("This presampled directory already exists")
        else:
            shutil.rmtree(base_dir)
    os.mkdir(base_dir)
    
    # Initiate datapackage
    datapackage = {
        "id": id_,
        "name": name,
        "profile": "data-package",
        "content": [],
        "resources": [],
        "description": description,
        }

    # inventory_elements
    if inventory_elements is not None:
        assert inventory_elements_samples is not None, "Cannot process inventory elements, missing information"
        assert len(inventory_elements)==inventory_elements_samples.shape[0], \
            "The number of inventory elements does not correspond to the number of inventory element samples"

        inv_dtype = [
            (numpy_string('input'), np.uint32),
            (numpy_string('output'), np.uint32),
            (numpy_string('row'), np.uint32),
            (numpy_string('col'), np.uint32),
            (numpy_string('type'), np.uint8),
        ]

        inventory_elements_arr = np.zeros(len(inventory_elements), dtype=inv_dtype)

        _ = lambda x: x if inventory_mapped else mapping[x]

        for i, row in enumerate(inventory_elements):
            processed = (_(row[0]), _(row[1]), MAX_INT_32, MAX_INT_32, TYPE_DICTIONARY[row[2]])
            inventory_elements_arr[i] = processed

        inventory_elements_fp = os.path.join(base_dir, "{}.inventory_elements.npy".format(id_))
        inventory_elements_samples_fp = os.path.join(base_dir, "{}.inventory_elements_samples.npy".format(id_))
        
        np.save(inventory_elements_fp, inventory_elements_arr, allow_pickle=False)
        np.save(inventory_elements_samples_fp, inventory_elements_samples.astype(np.float32), allow_pickle=False)

        datapackage['content'].append('inventory_elements')
        datapackage['resources'].extend(
            [{
                "name": "inventory_elements_samples",
                "path": "{}.inventory_elements_samples.npy".format(id_),
                "profile": "data-resource",
                "format": "npy",
                "mediatype": "application/octet-stream",
                "hash": md5(inventory_elements_samples_fp),
                "dtype": inventory_dtype,
                "shape": inventory_elements_samples.shape,
            },
            {
                "name": "inventory_elements",
                "path": "{}.inventory_elements.npy".format(id_),
                "profile": "data-resource",
                "format": "npy",
                "mediatype": "application/octet-stream",
                "hash": md5(inventory_elements_fp),
            }
            ])

    # cfs
    if cfs is not None:
        assert cfs_samples is not None, "Cannot process cfs, missing information"
        assert len(cfs)==cfs_samples.shape[0], \
            "The number of cfs does not correspond to the number of cf samples"

        ia_dtype = [
            (numpy_string('flow'), np.uint32),
            (numpy_string('row'), np.uint32),
        ]

        cfs_arr = np.zeros(len(cfs), dtype=ia_dtype)

        _ = lambda x: x if cfs_mapped else mapping[x]

        for i, row in enumerate(cfs):
            processed = (_(row), MAX_INT_32)
            cfs_arr[i] = processed

        cfs_fp = os.path.join(base_dir, "{}.cfs.npy".format(id_))
        cfs_samples_fp = os.path.join(base_dir, "{}.cfs_samples.npy".format(id_))
        
        np.save(cfs_fp, cfs, allow_pickle=False)
        np.save(cfs_samples_fp, cfs_samples.astype(np.float32), allow_pickle=False)

        datapackage['content'].append('cfs')
        datapackage['resources'].extend(
            [{
                "name": "cfs_samples",
                "path": "{}.cfs_samples.npy".format(id_),
                "profile": "data-resource",
                "format": "npy",
                "mediatype": "application/octet-stream",
                "hash": md5(cfs_samples_fp),
                "dtype": cfs_dtype,
                "shape": cfs_samples_fp.shape,
            },
            {
                "name": "cfs",
                "path": "{}.cfs.npy".format(id_),
                "profile": "data-resource",
                "format": "npy",
                "mediatype": "application/octet-stream",
                "hash": md5(cfs_fp),
            }
            ])
                
    if parameters is not None:
        assert parameters_samples is not None, "Exogenous parameters were passed, but parameter samples are missing."
        assert len(parameters)==parameters_samples.shape[0], "The number of exogenous parameters ({}) does not correspond to the number of samples {}".format(len(parameters), parameters_samples.shape[0])

        parameters_samples_fp = os.path.join(base_dir, "{}.parameters_samples.npy".format(id_))
        parameters_fp = os.path.join(base_dir, "{}.parameters.json".format(id_))
        
        with open(parameters_fp, "w") as f:
            json.dump(parameters, f)
        np.save(parameters_samples_fp, parameters_samples, allow_pickle=False)
        
        datapackage['content'].append('parameters')
        datapackage['resources'].extend(
            [
            {
                "name": "parameters_samples",
                "path": "{}.parameters_samples.npy".format(id_),
                "profile": "data-resource",
                "format": "npy",
                "mediatype": "application/octet-stream",
                "hash": md5(parameters_samples_fp),
                "dtype": parameters_dtype,
                "shape": parameters_samples.shape            
            }, {
                "name": "parameters",
                "path": "{}.parameters.json".format(id_),
                "profile": "data-resource",
                "format": "json",
                "mediatype": "application/json",
                "hash": md5(parameters_fp),
            }
            ])

    with open(os.path.join(base_dir, "datapackage.json"), "w") as f:
        json.dump(datapackage, f)

    return id_, base_dir

def convert_parameter_set_dict_to_presample_package(ps_dict, id_=None,
                                                    overwrite=None, 
                                                    forced_precision="float32"
                                                    ):
    if ps_dict.get('parameters'):
        parameters = ps_dict['parameters']
        parameters_samples = ps_dict['parameters_samples']
    else:
        parameters = None
        parameters_samples = None
    
    if ps_dict.get('inventory_elements'):
        inventory_elements = ps_dict['inventory_elements']
        inventory_elements_samples = ps_dict['inventory_elements_samples']
    else:
        inventory_elements = None
        inventory_elements_samples = None    
    
    if ps_dict.get('cfs'):
        inventory_elements = ps_dict['cfs']
        inventory_elements_samples = ps_dict['cfs_samples']
    else:
        cfs = None
        cfs_samples = None    
    
    id_, base_dir = create_presamples_package(inventory_elements=inventory_elements,
        inventory_elements_samples=inventory_elements_samples, inventory_dtype=forced_precision,
        cfs=cfs, cfs_samples=cfs_samples, cfs_dtype=forced_precision,
        parameters=parameters, parameters_samples=parameters_samples, parameters_dtype=forced_precision,
        id_=id_, overwrite=overwrite
        )
    return id_, base_dir
