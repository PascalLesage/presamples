from bw_presamples import *
from pathlib import Path
from scipy.sparse import *
import numpy as np
import pytest
import tempfile


@pytest.fixture
def arrays():
    with tempfile.TemporaryDirectory() as d:
        dirpath = Path(d)
        a = np.random.random(size=(5, 5))
        b = np.arange(10).reshape((2, 5))
        np.save(dirpath / "a.npy", a, allow_pickle=False)
        np.save(dirpath / "b.npy", b, allow_pickle=False)
        yield dirpath, a, b

@pytest.fixture
def dirpath():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

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
    assert ipa.sample(0).dtype == a.dtype
    assert ipa.sample(0).shape == (7,)
    possibles = [[0, 5], [1, 6], [2, 7], [3, 8], [4, 9]]
    assert ipa.sample(0)[:5].sum() < 5
    assert ipa.sample(0)[5:].tolist() in possibles

def test_reproducible_sampling(arrays):
    dirpath, a, b = arrays
    first = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))]
    )
    second = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))]
    )
    i = Indexer()
    for _ in range(100):
        index = next(i)
        f, s = first.sample(index), second.sample(index)
        assert np.allclose(f, s)

def test_reproducible_sampling_heterogeneous(dirpath):
    a = np.random.random(size=(500, 50))
    b = np.arange(100).reshape((25, 4))
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    np.save(dirpath / "b.npy", b, allow_pickle=False)
    first = IrregularPresamplesArray(
        [(dirpath / "a.npy", (500, 50)), (dirpath / "b.npy", (25, 4))]
    )
    second = IrregularPresamplesArray(
        [(dirpath / "a.npy", (500, 50)), (dirpath / "b.npy", (25, 4))]
    )
    i = Indexer()
    for _ in range(100):
        index = next(i)
        f, s = first.sample(index), second.sample(index)
        assert np.allclose(f, s)

def test_reproducible_sampling_single_column(dirpath):
    a = np.random.random(size=(500, 1))
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    ipa = IrregularPresamplesArray([(dirpath / "a.npy", (500, 1))])
    i = Indexer()
    for _ in range(100):
        assert ipa.sample(next(i)).shape == (500,)
        assert np.allclose(ipa.sample(next(i)), a.ravel())
