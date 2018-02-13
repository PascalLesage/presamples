from pathlib import Path
import json
import numpy as np
import os
import pytest
import tempfile

from bw_presamples import *
from bw_presamples.packaging import MAX_SIGNED_32BIT_INT
try:
    from bw2data import mapping
    from bw2data.tests import bw2test
except ImportError:
    bw2test = pytest.mark.skip


def update_hashes_from_given(given, expected):
    """Use hashes from written data to avoid hard-coding them."""
    for el1, el2 in zip(given['resources'], expected['resources']):
        el2['samples']['md5'] = el1['samples']['md5']
        if 'names' in el1:
            el2['names']['md5'] = el1['names']['md5']
        else:
            el2['indices']['md5'] = el1['indices']['md5']


@bw2test
def test_basic_packaging():
    mapping.add('ABCDEF')
    t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
    t2 = np.arange(12, dtype=np.int64).reshape((3, 4))
    b1 = [('A', 'D'), ('A', 'E'), ('B', 'F')]
    b2 = np.arange(12, dtype=np.int64).reshape((3, 4))
    c1 = 'DEF'
    c2 = np.arange(12, dtype=np.int64).reshape((3, 4))
    inputs = [
        (t2, t1, 'technosphere'),
        (b2, b1, 'biosphere'),
        (c2, c1, 'cf'),
    ]
    s1 = np.arange(16, dtype=np.int64).reshape((4, 4))
    s2 = np.arange(12, dtype=np.int64).reshape((3, 4))
    n1 = list('ABCD')
    n2 = list('DEF')
    id_, dirpath = create_presamples_package(
        inputs, [(s1, n1), (s2, n2)], name='foo', id_='bar'
    )
    assert id_ == 'bar'
    dirpath = Path(dirpath)
    expected = sorted([
        'bar.0.indices.npy', 'bar.0.samples.npy',
        'bar.1.indices.npy', 'bar.1.samples.npy',
        'bar.2.indices.npy', 'bar.2.samples.npy',
        'bar.3.names.json', 'bar.3.samples.npy',
        'bar.4.names.json', 'bar.4.samples.npy',
        'datapackage.json'
    ])
    assert sorted(os.listdir(dirpath)) == expected
    expected = np.arange(12, dtype=np.int64).reshape((3, 4))
    assert np.allclose(np.load(dirpath / 'bar.0.samples.npy'), expected)
    assert np.allclose(np.load(dirpath / 'bar.1.samples.npy'), expected)
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
    expected = np.arange(16, dtype=np.int64).reshape((4, 4))
    assert np.allclose(np.load(dirpath / 'bar.3.samples.npy'), expected)
    expected = ['A', 'B', 'C', 'D']
    assert json.load(open(dirpath / 'bar.3.names.json')) ==  expected
    expected = ['D', 'E', 'F']
    assert json.load(open(dirpath / 'bar.4.names.json')) ==  expected
    expected = {
        'id': 'bar',
        'name': 'foo',
        'profile': 'data-package',
        'resources': [{
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.0.samples.npy',
                'md5': None,
                'shape': [3, 4],
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'indices': {
                'filepath': 'bar.0.indices.npy',
                'md5': None,
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'matrix': 'technosphere_matrix',
            'row dict': '_product_dict',
            'row from label': 'input',
            'row to label': 'row',
            'col dict': '_activity_dict',
            'col from label': 'output',
            'col to label': 'col',
            'type': 'technosphere'
        }, {
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.1.samples.npy',
                'md5': None,
                'shape': [3, 4],
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'indices': {
                'filepath': 'bar.1.indices.npy',
                'md5': None,
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'matrix': 'biosphere_matrix',
            'row dict': '_biosphere_dict',
            'row from label': 'input',
            'row to label': 'row',
            'col dict': '_activity_dict',
            'col from label': 'output',
            'col to label': 'col',
            'type': 'biosphere'
        }, {
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.2.samples.npy',
                'md5': None,
                'shape': [3, 4],
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'indices': {
                'filepath': 'bar.2.indices.npy',
                'md5': None,
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'matrix': 'characterization_matrix',
            'row dict': '_biosphere_dict',
            'row from label': 'flow',
            'row to label': 'row',
            'type': 'cf'
        }, {
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.3.samples.npy',
                'md5': None,
                'shape': [4, 4],
                "format": "npy",
                "mediatype": "application/octet-stream"
            },
            'names': {
                'filepath': 'bar.3.names.json',
                'md5': None,
                "format": "json",
                "mediatype": "application/json"
            },
        }, {
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'bar.4.samples.npy',
                'md5': None,
                'shape': [3, 4],
                "format": "npy",
                "mediatype": "application/octet-stream"
            },
            'names': {
                'filepath': 'bar.4.names.json',
                'md5': None,
                "format": "json",
                "mediatype": "application/json"
            },
        }
    ]}
    given = json.load(open(dirpath / 'datapackage.json'))
    update_hashes_from_given(given, expected)
    assert given == expected

    # Test without optional fields
    create_presamples_package(inputs, [(s1, n1), (s2, n2)])
    create_presamples_package(matrix_presamples=inputs)
    create_presamples_package(inputs)
    create_presamples_package(parameter_presamples=[(s1, n1), (s2, n2)])

@bw2test
def test_basic_packaging_custom_directory():
    mapping.add('ABCDEF')
    t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
    t2 = np.arange(12).reshape((3, 4))
    inputs = [(t2, t1, 'technosphere')]

    with tempfile.TemporaryDirectory() as dirpath:
        assert len(list(os.listdir(dirpath))) == 0
        _, nd = create_presamples_package(
            inputs, name='foo', id_='bar', dirpath=dirpath
        )
        assert len(list(os.listdir(dirpath))) == 1
        assert len(list(os.listdir(nd))) == 3

@bw2test
def test_matrix_presamples_inconsistent_shape():
    mapping.add('ABCDEF')
    t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
    t2 = np.arange(12).reshape((3, 4))
    t3 = [('A', 'A', 0), ('A', 'B', 1)]
    t4 = np.arange(12).reshape((2, 6))
    inputs = [
        (t2, t1, 'technosphere'),
        (t4, t3, 'biosphere'),
    ]
    with pytest.raises(ValueError):
        create_presamples_package(inputs)

@bw2test
def test_parameter_presamples_inconsistent_shape():
    s1 = np.arange(16).reshape((4, 4))
    s2 = np.arange(12).reshape((2, 6))
    n1 = list('ABCD')
    n2 = list('DE')
    with pytest.raises(ValueError):
        create_presamples_package(parameter_presamples=[(s1, n1), (s2, n2)])

@bw2test
def test_matrix_shape_mismatch():
    s1 = np.arange(20).reshape((5, 4))
    n1 = list('ABC')
    with pytest.raises(ValueError):
        create_presamples_package([(s1, n1)])

@bw2test
def test_parameters_shape_mismatch():
    s1 = np.arange(16).reshape((4, 4))
    n1 = list('ABCDE')
    with pytest.raises(ValueError):
        create_presamples_package(parameter_presamples=[(s1, n1)])

@bw2test
def test_no_data_provided():
    with pytest.raises(ValueError):
        create_presamples_package(name='foo')

@bw2test
def test_incosistent_mc_numbers():
    mapping.add('ABCDEF')
    t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
    t2 = np.arange(12).reshape((3, 4))
    s1 = np.arange(16).reshape((4, 4))
    n1 = list('ABCD')
    create_presamples_package(
        [(t2, t1, 'technosphere')], [(s1, n1)], name='foo', id_='bar'
    )
    s1 = np.arange(20).reshape((4, 5))
    n1 = list('ABCDE')
    with pytest.raises(ValueError):
        create_presamples_package(
            [(t2, t1, 'technosphere')], [(s1, n1)], name='foo', id_='bar'
        )

@bw2test
def test_custom_metadata():
    mapping.add('ABCDEF')
    a = np.arange(12, dtype=np.int64).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'some_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'another_dict',
        'matrix': 'some_matrix'
    }
    frmt = lambda x: (x[0], x[1], 0, 0)
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    id_, dirpath = create_presamples_package(
        [(a, b, 'foo', dtype, frmt, metadata)],
        name='foo', id_='custom'
    )
    assert id_ == 'custom'
    dirpath = Path(dirpath)
    expected = sorted([
        'custom.0.indices.npy', 'custom.0.samples.npy',
        'datapackage.json'
    ])
    assert sorted(os.listdir(dirpath)) == expected
    expected = [
        (1, 1, 0, 0),
        (1, 2, 0, 0),
        (2, 3, 0, 0),
    ]
    assert np.load(dirpath / 'custom.0.indices.npy').tolist() ==  expected
    expected = {
        'id': 'custom',
        'name': 'foo',
        'profile': 'data-package',
        'resources': [{
            'profile': 'data-resource',
            'samples': {
                'dtype': 'int64',
                'filepath': 'custom.0.samples.npy',
                'md5': None,
                'shape': [3, 4],
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'indices': {
                'filepath': 'custom.0.indices.npy',
                'md5': None,
                'format': 'npy',
                'mediatype': 'application/octet-stream',
            },
            'matrix': 'some_matrix',
            'row dict': 'some_dict',
            'row from label': 'f1',
            'row to label': 'f3',
            'col dict': 'another_dict',
            'col from label': 'f2',
            'col to label': 'f4',
            'type': 'foo'
        }
    ]}
    given = json.load(open(dirpath / 'datapackage.json'))
    update_hashes_from_given(given, expected)
    assert given == expected

@bw2test
def test_custom_metadata_error():
    a = np.arange(12).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'some_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'another_dict',
        'matrix': 'some_matrix'
    }
    frmt = lambda x: (x[0], x[1], 0, 0)
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    create_presamples_package(
        [(a, b, 'foo', dtype, frmt, metadata)]
    )
    # Missing `row to label`
    metadata = {
        'row from label': 'f1',
        'row dict': 'some_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'another_dict',
        'matrix': 'some_matrix'
    }
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', dtype, frmt, metadata)]
        )
    # No cols is OK
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'some_dict',
        'matrix': 'some_matrix'
    }
    create_presamples_package(
        [(a, b, 'foo', dtype, frmt, metadata)]
    )
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'some_dict',
        'col from label': 'f2',
        'col dict': 'another_dict',
        'matrix': 'some_matrix'
    }
    # Missing `col to label`
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', dtype, frmt, metadata)]
        )
    metadata = {
        'row from label': 'f5',
        'row to label': 'f3',
        'row dict': 'some_dict',
        'matrix': 'some_matrix'
    }
    # Missing `f5` field in indices
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', dtype, frmt, metadata)]
        )

@bw2test
def test_missing_formatter():
    a = np.arange(12).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    with pytest.raises(KeyError):
        create_presamples_package([(a, b, 'foo')])

@bw2test
def test_incomplete_custom_metadata():
    a = np.arange(12).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f2',
        'row dict': 'some_dict',
        'matrix': 'some_matrix'
    }
    frmt = lambda x: x
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
    ]
    create_presamples_package(
        [(a, b, 'foo', dtype, frmt, metadata)]
    )
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', None, frmt, metadata)]
        )
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', dtype, None, metadata)]
        )
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', dtype, frmt, None)]
        )

@bw2test
def test_overwrite():
    mapping.add('ABCDEF')
    t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
    t2 = np.arange(12).reshape((3, 4))
    inputs = [(t2, t1, 'technosphere')]
    create_presamples_package(inputs, name='foo', id_='bar')
    with pytest.raises(ValueError):
        create_presamples_package(
            inputs, name='foo', id_='bar'
        )
    create_presamples_package(inputs, name='foo', id_='bar', overwrite=True)

@bw2test
def test_shape_mismatch():
    a = np.arange(12).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f2',
        'row dict': 'some_dict',
        'matrix': 'some_matrix'
    }
    frmt = lambda x: x
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
    ]
    create_presamples_package(
        [(a, b, 'foo', dtype, frmt, metadata)]
    )
    a = np.arange(20).reshape((5, 4))
    with pytest.raises(ValueError):
        create_presamples_package(
            [(a, b, 'foo', dtype, frmt, metadata)]
        )

def test_split_inventory_presamples():
    a = np.arange(20).reshape((4, 5))
    b = [
        (1, 2, 'technosphere'),
        (3, 4, 'biosphere'),
        (5, 6, 'random'),
        (7, 8, 'production'),
    ]
    (u, v, w), (x, y, z) = split_inventory_presamples(a, b)
    assert np.allclose(np.arange(5, 10), u)
    assert np.allclose(np.arange(20).reshape((4, 5))[(0, 2, 3), :], x)
    assert v == [(3, 4)]
    assert y == [(1, 2, 'technosphere'), (5, 6, 'random'), (7, 8, 'production')]
    assert w == 'biosphere'
    assert z == 'technosphere'

def test_split_inventory_presamples_drop_empty():
    a = np.arange(15).reshape((3, 5))
    b = [
        (1, 2, 'technosphere'),
        (5, 6, 'random'),
        (7, 8, 'production'),
    ]
    lst = split_inventory_presamples(a, b)
    assert len(lst) == 1
    (x, y, z) = lst[0]
    assert y == [(1, 2, 'technosphere'), (5, 6, 'random'), (7, 8, 'production')]
    assert z == 'technosphere'

def tests_split_inventory_presamples_error():
    with pytest.raises(AssertionError):
        split_inventory_presamples(None, [])
    a = np.arange(20).reshape((4, 5))
    b = list(range(5))
    with pytest.raises(AssertionError):
        split_inventory_presamples(a, b)

def test_split_inventory_presamples_integer_types():
    a = np.arange(20).reshape((4, 5))
    b = [
        (1, 2, 1),
        (3, 4, 2),
        (5, 6, 7),
        (7, 8, 0),
    ]
    (u, v, w), (x, y, z) = split_inventory_presamples(a, b)
    assert np.allclose(np.arange(5, 10), u)
    assert np.allclose(np.arange(20).reshape((4, 5))[(0, 2, 3), :], x)
    assert v == [(3, 4)]
    assert y == [(1, 2, 1), (5, 6, 7), (7, 8, 0)]
    assert w == 'biosphere'
    assert z == 'technosphere'
