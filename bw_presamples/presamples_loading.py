# -*- coding: utf-8 -*-
from eight import *

from bw2calc.indexing import index_with_arrays as _
from bw2calc.matrices import TechnosphereBiosphereMatrixBuilder as MB
from bw2calc.utils import md5
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


class IrregularPresamplesArray(object):
    """A wrapper around a list of memory-mapped Numpy arrays with heterogeneous shapes.

    This class provides a simple way to consistently sample arrays with different shapes and datatypes.

    Input arguments:

    * ``filepaths``: An iterable of (Numpy array filepath, shape as tuple).
    * ``seed``: Seed for RNG. Optional.

    """
    def __init__(self, filepaths, seed=None):
        self.seed = seed
        np.random.seed(seed)

        self.data = [
            (np.load(fp, mmap_mode='r'), shape[1])
            for fp, shape in filepaths
        ]

    def sample(self):
        """Draw a new sample from the pre-sample arrays"""
        # TODO: fix max value to MAX_SIGNED_INT_32 after merging
        index = np.random.randint(0, 2147483647)
        arr = np.hstack([arr[:, index % ncols] for arr, ncols in self.data])
        return np.hstack([arr[:, index % ncols] for arr, ncols in self.data])


class Presamples(object):
    """Class that efficiently handles arrays of presampled arrays.
    Presampled arrays can contain any of the following types of data:
        - Inventory matrix elements that can be inserted in LCA matrices during calculations.
        - Characterization factors  that can be inserted in LCA matrices during calculations.
        - Exogenous parameters.

    Presampled arrays are provided as a list of directory paths. Each directory contains a datapackage file: 

    * ``datapackage.json``: A JSON file following the `datapackage standard <http://frictionlessdata.io/guides/data-package/>`__ that indicates the provenance of the data. The specific content of the datapackage will depend on what the presamples contains.
    All datapackage.json files should minimally have the following information:

    .. code-block:: json

        {
          "id": uuid,
          "profile": "data-package",
          "content": list describing what type of data is found in the presamples ("inventory_elements", "cfs", or "parameters"). If empty, the presamples is empty.
          "resources": list of resources, which depends on the presamples content.
        }

    If the presamples contains inventory matrix elements, the ``resources`` list will contain the following two dictionaries:
    .. code-block:: json
            {
              "name": "inventory_elements_samples",
              "path": "{id}.inventory_elements_samples.npy",
              "profile": "data-resource",
              "format": "npy",
              "mediatype": "application/octet-stream",
              "hash": md5 hash,
              "dtype": dtype,
              "shape": [rows, columns]
            },
            {
              "name": "parameters",
              "path": "{uuid}.params.npy",
              "profile": "data-resource",
              "format": "npy",
              "mediatype": "application/octet-stream",
              "hash": md5 hash,
            },
          ]
        }

    The presamples directory will then contain the following two files: 
    * ``{uuid}.inventory_elements_samples.npy``: Array of samples values in `npy format <https://docs.scipy.org/doc/numpy-dev/neps/npy-format.html>`__.
    * ``{uuid}.inventory_elements.npy``: A Numpy `record array <https://docs.scipy.org/doc/numpy/reference/generated/numpy.recarray.html>`__ in ``npy`` format with the following columns:
        * ``input``: uint32
        * ``output``: uint32
        * ``row``: uint32
        * ``col``: uint32
        * ``type``: uint8

    ``type`` is an integer in ``bw2data.utils.TYPE_DICTIONARY`` that indicates whether the modified exchange is an consumer, producer, or emission.

    If the presamples contains characterization factors, the ``resources`` list will contain the following two dictionaries:
    
    .. code-block:: json
            {
              "name": "cfs_samples",
              "path": "{id}.cfs_samples.npy",
              "profile": "data-resource",
              "format": "npy",
              "mediatype": "application/octet-stream",
              "hash": md5 hash,
              "dtype": dtype,
              "shape": [rows, columns]
            },
            {
              "name": "cfs",
              "path": "{id}.cfs.npy",
              "profile": "data-resource",
              "format": "npy",
              "mediatype": "application/octet-stream",
              "hash": md5 hash,
            },
          ]
        }

    The presamples directory will then contain the following two files: 
    * ``{uuid}.cfs_samples.npy``: Array of samples values in `npy format <https://docs.scipy.org/doc/numpy-dev/neps/npy-format.html>`__.
    * ``{uuid}.cfs.npy``: A Numpy `record array <https://docs.scipy.org/doc/numpy/reference/generated/numpy.recarray.html>`__ in ``npy`` format with the following columns:
        * ``flow``: uint32
        * ``row``: uint32

    If the presamples contains exogenous parameters, which can be used in e.g. sensitivity analyses, the ``resources`` list will contain the following two dictionaries:
    
    .. code-block:: json
    
        {
            "name": "parameters_samples",
            "path": "{uuid}.parameters_samples.npy",
            "profile": "data-resource",
            "format": "npy",
            "mediatype": "application/octet-stream",
            "hash": md5 hash,
            "dtype": dtype,
            "shape": [rows, columns]            
        }, {
            "name": "parameters",
            "path": "{uuid}.parameters.json",
            "profile": "data-resource",
            "format": "json",
            "mediatype": "application/json",
            "hash": md5 hash,
        }
        
    The metadata is loaded and concatenated. Input and output values for LCA matrix elements are mapped to the correct row and column indices.

    The samples arrays are not loaded into memory, but memory mapped to reduce resource consumption. As such, they are not concatenated.

    Normal life cycle for this class:

    * Instantiate with some directory paths and (optionally) a random seed
    ?? NO LONGER RELEVANT??* Index the parameter arrays with ``index_arrays``.
    * For each Monte Carlo iteration, generate new matrices, and then update them using the ``update_inventory`` and ``update_cfs`` functions.

    Note that we currently assume that all values will be present in the built matrix. Silent errors or losses in efficiency could happen if this assumption does not hold!

    """
    def __init__(self, dirpaths, seed=None):
        data = []

        for dirpath in (dirpaths or []):
            Presamples.validate_dirpath(dirpath)
            data.extend(Presamples.load_presamples(dirpath))

        self.empty = not bool(data)
        if self.empty:
            return

        self.tech_params, self.bio_params, self.tech_mask, self.bio_mask, \
            self.inventory_samples = Presamples.get_inventory(data)
        self.cf_params, self.cf_samples = Presamples.get_cfs(data)
        self.exogenous_parameters, self.exogenous_parameters_samples = Presamples.get_exogenous(data)

    @staticmethod
    def validate_dirpath(dirpath):
        assert os.path.isdir(dirpath)
        files = list(os.listdir(dirpath))
        assert "datapackage.json" in files, "{} missing a datapackage file".format(dirpath)
        metadata = json.load(
            open(os.path.join(dirpath, "datapackage.json")),
            encoding="utf-8"
        )        
        stored_data_types = metadata['content']
        if 'inventory_elements' in stored_data_types:
            assert any("inventory_elements_samples.npy" in x for x in files),\
                "Expected inventory element samples for {} missing".format(dirpath)
            assert any("inventory_elements.npy" in x for x in files),\
                "Expected inventory elements for {} missing".format(dirpath)
        if 'cfs' in stored_data_types:
            assert any("cfs_samples.npy" in x for x in files),\
                "Expected cfs samples for {} missing".format(dirpath)
            assert any("cfs.npy" in x for x in files),\
                "Expected cfs for {} missing".format(dirpath)
        if 'parameters' in stored_data_types:
            assert any("parameters_samples.npy" in x for x in files),\
                "Expected exogenous parameters samples for {} missing".format(dirpath)
            assert any("parameters.json" in x for x in files),\
                "Expected exogenous parameter names for {} missing".format(dirpath)

    @staticmethod
    def load_presamples(dirpath):
        metadata = json.load(
            open(os.path.join(dirpath, "datapackage.json")),
            encoding="utf-8"
        )
        
        returned = []
        
        stored_data_types = metadata['content']

        if 'inventory_elements' in stored_data_types:
            samples_md = [x for x in metadata['resources'] if x['name'] == 'inventory_elements_samples'][0]            
            samples_fp = os.path.abspath(os.path.join(dirpath, samples_md['path']))            
            assert md5(samples_fp) == samples_md['hash']

            elements_md = [x for x in metadata['resources'] if x['name'] == 'inventory_elements'][0]    
            elements_fp = os.path.abspath(os.path.join(dirpath, elements_md['path']))
            assert md5(elements_fp) == elements_md['hash']
            
            returned.append(
                {
                'stored_data_type': 'inventory_elements',
                'params': np.load(elements_fp),
                'samples': {
                    'filepath': samples_fp,
                    'shape': samples_md['shape'],
                    }
                }
                )

        if 'cfs' in stored_data_types:
            samples_md = [x for x in metadata['resources'] if x['name'] == 'cfs_samples'][0]            
            samples_fp = os.path.abspath(os.path.join(dirpath, samples_md['path']))            
            assert md5(samples_fp) == samples_md['hash']

            cfs_md = [x for x in metadata['resources'] if x['name'] == 'cfs'][0]    
            cfs_fp = os.path.abspath(os.path.join(dirpath, cfs_md['path']))
            assert md5(cfs_fp) == cfs_md['hash']
            
            returned.append(
                {
                'stored_data_type': 'cfs',
                'params': np.load(cfs_fp),
                'samples': {
                    'filepath': samples_fp,
                    'shape': samples_md['shape'],
                    }
                }
                )

        if 'parameters' in stored_data_types:
            samples_md = [x for x in metadata['resources'] if x['name'] == 'parameters_samples'][0]            
            samples_fp = os.path.abspath(os.path.join(dirpath, samples_md['path']))            
            assert md5(samples_fp) == samples_md['hash']

            parameters_md = [x for x in metadata['resources'] if x['name'] == 'parameters'][0]    
            parameters_fp = os.path.abspath(os.path.join(dirpath, parameters_md['path']))
            assert md5(parameters_fp) == parameters_md['hash']
            
            with open(parameters_fp, 'r') as f:
                parameters = json.load(f)

            returned.append(
                {
                'stored_data_type': 'parameters',
                'parameters': parameters,
                'samples': {
                    'filepath': samples_fp,
                    'shape': samples_md['shape'],
                    }
                }
                )
        
        return returned

    @staticmethod
    def get_inventory(data):
        selection = [x for x in data if x['stored_data_type'] == 'inventory_elements']
        if selection:
            samples = IrregularPresamplesArray([
                (x['samples']['filepath'], x['samples']['shape'])
                for x in selection
            ])
            params = np.hstack([x['params'] for x in selection])
            return (
                MB.select_technosphere_array(params),
                MB.select_biosphere_array(params),
                MB.get_technosphere_inputs_mask(params),
                MB.get_biosphere_inputs_mask(params),
                samples,
            )
        else:
            return None, None, None, None, None


    @staticmethod
    def get_cfs(data):
        selection = [x for x in data if x['stored_data_type'] == 'cfs']
        if selection:
            samples = IrregularPresamplesArray([
                (x['samples']['filepath'], x['samples']['shape'])
                for x in selection
            ])
            params = np.hstack([x['params'] for x in selection])
            return params, samples
        else:
            return None, None

    @nonempty
    def index_inv_arrays(self, activity_dict, product_dict, flow_dict):
        try:
            _(self.tech_params['input'], self.tech_params['row'], product_dict)
            _(self.tech_params['output'], self.tech_params['col'], activity_dict)
        except:
            pass
        try:   
            _(self.bio_params['input'], self.bio_params['row'], flow_dict)
            _(self.bio_params['output'], self.bio_params['col'], product_dict)
        except:
            pass

    @nonempty
    def index_ia_arrays(self, flow_dict):
        try:
            _(self.cf_params['flow'], self.cf_params['row'], flow_dict)
        except:
            pass

    @nonempty
    def update_inventory(self, technosphere, biosphere):
        sample = self.inventory_samples.sample()
        try:
            tech_sample = sample[self.tech_mask]
            MB.fix_supply_use(self.tech_params, tech_sample)
            technosphere[self.tech_params['row'], self.tech_params['col']] = tech_sample

        except:
            pass
        try:
            bio_sample = sample[self.bio_mask]
            biosphere[self.bio_params['row'], self.bio_params['col']] = bio_sample
        except:
            pass

    @nonempty
    def update_cfs(self, matrix):
        try:
            matrix[self.cf_params['row'], self.cf_params['row']] = self.cf_samples.sample()
        except:
            pass

    @staticmethod
    def get_exogenous(data):
        parameters = []
        selection = [x for x in data if x['stored_data_type'] == 'parameters']
        if selection:
            for x in selection:
                parameters.extend(x['parameters'])
            parameters_samples = IrregularPresamplesArray([
                    (x['samples']['filepath'], x['samples']['shape'])
                    for x in selection
            ])
            return parameters, parameters_samples
        else:
            return None, None

    @nonempty
    def return_exogenous_parameters_and_samples(self, iterations):
        rows = len(self.exogenous_parameters)
        exogenous_parameters_samples = np.empty([rows, iterations])
        for iteration in range(iterations):
            exogenous_parameters_samples[:, iteration] = self.exogenous_parameters_samples.sample()
        return self.exogenous_parameters, exogenous_parameters_samples