from bw_presamples.models import FixedSum
import numpy as np
import pytest


def test_fixed_sum_basic():
    fs =  FixedSum([
        {'uncertainty type': 0, 'amount': 4.2},
        {'uncertainty type': 4, 'amount': 3, 'minimum': 1, 'maximum': 6},
        {'uncertainty type': 4, 'amount': 2.8, 'minimum': 2, 'maximum': 3.6}
    ], iterations=10)
    fs.run()
    assert np.allclose(np.ones((10,)) * 10, fs.array.sum(axis=0))
    assert np.allclose(np.ones((10,)) * 4.2, fs.array[0, :])
    assert np.unique(fs.array[1:, :]).shape == (20,)

def test_fixed_sum_filling():
    fs =  FixedSum([
        {'amount': 4.2},
        {'uncertainty type': 4, 'amount': 3, 'minimum': 1, 'maximum': 6},
        {'uncertainty type': 4, 'amount': 2.8, 'minimum': 2, 'maximum': 3.6}
    ], iterations=10)
    assert fs.data[0] == {'uncertainty type': 0, 'amount': 4.2, 'loc': 4.2}
    for row in fs.data:
        assert row['loc'] == row['amount']

def test_fixed_sum_rescale_fixed():
    fs =  FixedSum([
        {'uncertainty type': 0, 'amount': 4.2},
        {'uncertainty type': 4, 'amount': 3, 'minimum': 1, 'maximum': 6},
        {'uncertainty type': 4, 'amount': 2.8, 'minimum': 2, 'maximum': 3.6}
    ], rescale_fixed=True, iterations=10)
    fs.run()
    assert np.allclose(np.ones((10,)) * 10, fs.array.sum(axis=0))
    assert not np.allclose(np.ones((10,)) * 4.2, fs.array[0, :])
    assert np.unique(fs.array[:, :]).shape == (30,)

def test_fixed_sum_error():
    with pytest.raises(ValueError):
        FixedSum([
            {'uncertainty type': 0, 'amount': 4.2},
            {'uncertainty type': 4, 'amount': 3, 'minimum': 1, 'maximum': 6},
            {'uncertainty type': 4, 'amount': 2.8, 'minimum': 2, 'maximum': 3.6}
        ], rescale_fixed=False, expected_sum=2, iterations=10)

def test_fixed_sum_expected_sum():
    fs =  FixedSum([
        {'uncertainty type': 0, 'amount': 4.2},
        {'uncertainty type': 4, 'amount': 3, 'minimum': 1, 'maximum': 6},
        {'uncertainty type': 4, 'amount': 2.8, 'minimum': 2, 'maximum': 3.6}
    ], rescale_fixed=True, expected_sum=5, iterations=10)
    fs.run()
    assert np.allclose(np.ones((10,)) * 5, fs.array.sum(axis=0))
    assert np.unique(fs.array[:, :]).shape == (30,)

def test_fixed_sum_expected_sum_negative():
    fs =  FixedSum([
        {'uncertainty type': 0, 'amount': 4.2},
        {'uncertainty type': 4, 'amount': 3, 'minimum': 1, 'maximum': 6},
        {'uncertainty type': 4, 'amount': 2.8, 'minimum': 2, 'maximum': 3.6}
    ], rescale_fixed=True, expected_sum=-5, iterations=10)
    fs.run()
    assert np.allclose(np.ones((10,)) * -5, fs.array.sum(axis=0))
    assert np.unique(fs.array[:, :]).shape == (30,)
