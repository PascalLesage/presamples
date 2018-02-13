from scipy.sparse import *
import numpy as np


def test_duplicate_entries_uses_last_one():
    m = dok_matrix((5, 5))
    for i in range(5):
         for j in range(5):
             m[i, j] = 0

    a = np.array((1, 2, 2))
    b = np.array((2, 2, 2))
    c = np.array((10, 11, 12))
    m[a, b] = c

    assert m[1, 2] == 10
    assert m[2, 2] == 12
