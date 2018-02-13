from bw_presamples.models import KroneckerDelta
import numpy as np
import pytest


def test_kronecker_missing_amount():
    with pytest.raises(KeyError):
        KroneckerDelta([
            {'amount': 4.2},
            {}
        ]).run()

def test_kronecker_basic():
    k =  KroneckerDelta([{'amount': 1}, {'amount': 3}, {'amount': 6},], iterations=1000)
    k.run()
    assert isinstance(k.matrix_array, np.ndarray)
    assert k.matrix_array.shape == ((3, 1000))
    sums = k.matrix_array.sum(axis=1)
    assert sums[0] < sums[1] < sums[2]
    assert set(np.unique(k.matrix_array)) == {0, 1}
    assert np.allclose(k.matrix_array.sum(axis=0), np.ones((1000,)))

def test_kronecker_no_normalize():
    k =  KroneckerDelta([{'amount': 1}, {'amount': 3}, {'amount': 6},], iterations=1000, normalize=False)
    k.run()
    assert isinstance(k.matrix_array, np.ndarray)
    assert k.matrix_array.shape == ((3, 1000))
    sums = k.matrix_array.sum(axis=1)
    assert sums[0] < sums[1] < sums[2]
    assert set(np.unique(k.matrix_array)) == {0, 1, 3, 6}
    assert set(np.unique(k.matrix_array[1, :])) == {0, 3}

def test_kronecker_equal_choice():
    k =  KroneckerDelta([{'amount': 1}, {'amount': 3}, {'amount': 6},], iterations=10000, equal_choice=True)
    k.run()
    assert isinstance(k.matrix_array, np.ndarray)
    assert k.matrix_array.shape == ((3, 10000))
    sums = k.matrix_array.sum(axis=1)
    for x in range(3):
        assert 2500 < sums[x] < 4000
    assert set(np.unique(k.matrix_array)) == {0, 1}
    assert np.allclose(k.matrix_array.sum(axis=0), np.ones((10000,)))

def test_kronecker_negative():
    k =  KroneckerDelta([{'amount': 1}, {'amount': -3}, {'amount': 6},], iterations=1000)
    k.run()
    assert isinstance(k.matrix_array, np.ndarray)
    assert k.matrix_array.shape == ((3, 1000))
    sums = k.matrix_array.sum(axis=1)
    assert sums[1] < sums[0] < sums[2]
    assert set(np.unique(k.matrix_array)) == {0, 1, -1}
    assert set(np.unique(k.matrix_array[1, :])) == {0, -1}
