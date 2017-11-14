from bw_presamples import *
from scipy.sparse import *
import numpy as np
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def arrays():
    dirpath = Path(tempfile.mkdtemp())
    a = np.random.random(size=(5, 5))
    b = np.arange(10).reshape((2, 5))
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    np.save(dirpath / "b.npy", b, allow_pickle=False)
    return dirpath, a, b

def test_seed(arrays):
    dirpath, a, b = arrays
    ipa = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))]
    )
    assert ipa.seed_value is None
    ipa = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))], 42
    )
    assert ipa.seed_value == 42

def test_loading(arrays):
    dirpath, a, b = arrays
    ipa = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))]
    )
    (h, i), (j, k) = ipa.data
    assert np.allclose(a, h)
    assert np.allclose(b, j)
    assert i == 5
    assert k == 5

def test_sampling(arrays):
    dirpath, a, b = arrays
    ipa = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))]
    )
    assert ipa.sample().dtype == a.dtype
    assert ipa.sample().shape == (7,)
    possibles = [[0, 5], [1, 6], [2, 7], [3, 8], [4, 9]]
    assert ipa.sample()[:5].sum() < 5
    assert ipa.sample()[5:].tolist() in possibles

def test_reproducible_sampling(arrays):
    dirpath, a, b = arrays
    first = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))], 111
    )
    second = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))], 111
    )
    for _ in range(100):
        f, s = first.sample(), second.sample()
        assert np.allclose(f, s)

def test_reproducible_sampling_heterogeneous():
    dirpath = Path(tempfile.mkdtemp())
    a = np.random.random(size=(500, 50))
    b = np.arange(100).reshape((25, 4))
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    np.save(dirpath / "b.npy", b, allow_pickle=False)
    first = IrregularPresamplesArray(
        [(dirpath / "a.npy", (500, 50)), (dirpath / "b.npy", (25, 4))], 111
    )
    second = IrregularPresamplesArray(
        [(dirpath / "a.npy", (500, 50)), (dirpath / "b.npy", (25, 4))], 111
    )
    for _ in range(100):
        f, s = first.sample(), second.sample()
        assert np.allclose(f, s)

def test_reproducible_sampling_single_column():
    dirpath = Path(tempfile.mkdtemp())
    a = np.random.random(size=(500, 1))
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    ipa = IrregularPresamplesArray([(dirpath / "a.npy", (500, 1))])
    for _ in range(100):
        assert ipa.sample().shape == (500,)
        assert np.allclose(ipa.sample(), a.ravel())
