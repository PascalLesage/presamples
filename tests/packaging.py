from bw2data import mapping
from bw2data.tests import bw2test
from bw_presamples import create_matrix_presamples_package
from bw_presamples.packaging import MAX_SIGNED_32BIT_INT
from pathlib import Path
import json
import numpy as np
import os
import pytest


TYPE_DICTIONARY = {
    "unknown": -1,
    "production": 0,
    "technosphere": 1,
    "biosphere": 2,
    "substitution": 3,
}

@bw2test
def test_basic_packaging():
    mapping.add('ABCDEF')
    t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
    t2 = np.arange(12).reshape((3, 4))
    b1 = [('A', 'D'), ('A', 'E'), ('B', 'F')]
    b2 = np.arange(15).reshape((3, 5))
    c1 = 'DEF'
    c2 = np.arange(18).reshape((3, 6))
    inputs = [
        (t2, t1, 'technosphere'),
        (b2, b1, 'biosphere'),
        (c2, c1, 'cf'),
    ]
    id_, dirpath = create_matrix_presamples_package(inputs, name='foo', id_='bar')
    assert id_ == 'bar'
    dirpath = Path(dirpath)
    expected = [
        'bar.0.indices.npy', 'bar.0.samples.npy',
        'bar.1.indices.npy', 'bar.1.samples.npy',
        'bar.2.indices.npy', 'bar.2.samples.npy',
        'datapackage.json'
    ]
    assert list(os.listdir(dirpath)) == expected
    expected = np.arange(12).reshape((3, 4))
    assert np.allclose(np.load(dirpath / 'bar.0.samples.npy'), expected)
    expected = np.arange(15).reshape((3, 5))
    assert np.allclose(np.load(dirpath / 'bar.1.samples.npy'), expected)
    expected = np.arange(18).reshape((3, 6))
    assert np.allclose(np.load(dirpath / 'bar.2.samples.npy'), expected)
    expected = [
        (1, 1, MAX_SIGNED_32BIT_INT, MAX_SIGNED_32BIT_INT, 0),
        (1, 2, MAX_SIGNED_32BIT_INT, MAX_SIGNED_32BIT_INT, 1),
        (2, 3, MAX_SIGNED_32BIT_INT, MAX_SIGNED_32BIT_INT, 3),
    ]
    assert np.load(dirpath / 'bar.0.indices.npy').tolist() ==  expected
    expected = [
        (1, 4, MAX_SIGNED_32BIT_INT, MAX_SIGNED_32BIT_INT),
        (1, 5, MAX_SIGNED_32BIT_INT, MAX_SIGNED_32BIT_INT),
        (2, 6, MAX_SIGNED_32BIT_INT, MAX_SIGNED_32BIT_INT),
    ]
    assert np.load(dirpath / 'bar.1.indices.npy').tolist() ==  expected
    expected = [
        (4, MAX_SIGNED_32BIT_INT),
        (5, MAX_SIGNED_32BIT_INT),
        (6, MAX_SIGNED_32BIT_INT),
    ]
    assert np.load(dirpath / 'bar.2.indices.npy').tolist() ==  expected
    expected = {
        'id': 'bar',
        'name': 'foo',
        'profile': 'data-package',
        'resources': [{
            'format': 'npy',
            'mediatype': 'application/octet-stream',
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.0.samples.npy',
                'md5': '1d1de948043b8e205e1d6390f67d6ee5',
                'shape': [3, 4]
            },
            'indices': {
                'filepath': 'bar.0.indices.npy',
                'md5': '781ccec1f551faeb0c082fc40e1ee1fa'
            },
            'matrix': 'technosphere_matrix',
            'row dict': 'product_dict',
            'row from label': 'input',
            'row to label': 'row',
            'col dict': 'activity_dict',
            'col from label': 'output',
            'col to label': 'col',
            'type': 'technosphere'
        }, {
            'format': 'npy',
            'mediatype': 'application/octet-stream',
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.1.samples.npy',
                'md5': '65bf1e51e87170e5ce6fb65f7f1a56e2',
                'shape': [3, 5]
            },
            'indices': {
                'filepath': 'bar.1.indices.npy',
                'md5': '82fed4a68bafab13a03bb99e5044c227'
            },
            'matrix': 'biosphere_matrix',
            'row dict': 'biosphere_dict',
            'row from label': 'input',
            'row to label': 'row',
            'col dict': 'activity_dict',
            'col from label': 'output',
            'col to label': 'col',
            'type': 'biosphere'
        }, {
            'format': 'npy',
            'mediatype': 'application/octet-stream',
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.2.samples.npy',
                'md5': '75e9b72fbe786e7887e4f29669ebd584',
                'shape': [3, 6]
            },
            'indices': {
                'filepath': 'bar.2.indices.npy',
                'md5': '5a55dded5bf1e878b457a2756aa11f00'
            },
            'matrix': 'characterization_matrix',
            'row dict': 'biosphere_dict',
            'row from label': 'flow',
            'row to label': 'row',
            'type': 'cf'
        }
    ]}
    assert json.load(open(dirpath / 'datapackage.json')) == expected

@bw2test
def test_custom_metadata():
    pass

@bw2test
def test_overwrite():
    pass

@bw2test
def test_formatting_errors():
    pass

@bw2test
def test_shape_mismatch():
    pass
