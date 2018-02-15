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

def test_sampling_no_seed_different_each_time(arrays):
    dirpath, a, b = arrays
    ipa = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5)), (dirpath / "b.npy", (2, 5))]
    )
    samples = [ipa.sample() for _ in range(20)]
    count = sum([np.allclose(samples[i], samples[i + 1]) for i in range(19)])
    assert count < 10

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

def test_reproducible_sampling_heterogeneous(dirpath):
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

def test_reproducible_sampling_single_column(dirpath):
    a = np.random.random(size=(500, 1))
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    ipa = IrregularPresamplesArray([(dirpath / "a.npy", (500, 1))])
    for _ in range(100):
        assert ipa.sample().shape == (500,)
        assert np.allclose(ipa.sample(), a.ravel())

def test_sequential_seed(dirpath):
    a = np.ones((5, 5))
    for i in range(5):
        a[:, i] *= i
    np.save(dirpath / "a.npy", a, allow_pickle=False)
    ipa = IrregularPresamplesArray(
        [(dirpath / "a.npy", (5, 5))], "sequential"
    )
    assert ipa.seed_value == None
    assert ipa.count == 0
    for i in range(5):
        assert ipa.count == i
        assert np.allclose(ipa.sample(), np.ones(5) * i)
        assert ipa.count == i + 1
