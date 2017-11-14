from bw_presamples import *
from scipy.sparse import *
import numpy as np
import pytest
from bw2data.tests import bw2test


class MockLCA:
    def __init__(self):
        self.matrix = dok_matrix((5, 5))
        for i in range(5):
             for j in range(5):
                 self.matrix[i, j] = 0
        self.row_dict = {x: 2 * x for x in range(5)}
        self.col_dict = {x: 3 * x for x in range(5)}


def test_update_matrices():
    a = np.ones(shape=(3, 4)) * 100
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'matrix'
    }
    frmt = lambda x: (x[0], x[1], x[0], x[1])
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    id_, dirpath = create_presamples_package(
        [(a, b, 'mock', dtype, frmt, metadata)],
    )
    mp = MatrixPresamples([dirpath])
    lca = MockLCA()
    mp.update_matrices(lca)
    assert lca.matrix[1, 1] == 100
    assert lca.matrix[1, 2] == 100
    assert lca.matrix[2, 3] == 100
    assert lca.matrix.sum() == 300

def test_index_arrays():
    a = np.ones(shape=(3, 4)) * 100
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'matrix'
    }
    frmt = lambda x: (x[0], x[1], 0, 0)
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    id_, dirpath = create_presamples_package(
        [(a, b, 'mock', dtype, frmt, metadata)],
    )
    mp = MatrixPresamples([dirpath])
    lca = MockLCA()
    mp.index_arrays(lca)
    expected = [(1, 1, 2, 3), (1, 2, 2, 6), (2, 3, 4, 9)]
    assert mp.data[0]['resources'][0]['indices'].tolist() == expected
