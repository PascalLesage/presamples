from presamples import Indexer
from pathlib import Path
from scipy.sparse import *
import numpy as np
import pytest
import tempfile


def test_seed():
    i = Indexer(1e6)
    assert i.seed_value is None
    i = Indexer(1e6, seed=42)
    assert i.seed_value == 42

def test_ncols():
    i = Indexer(1e6)
    assert i.ncols == 1e6

def test_sequential_wraparound():
    i = Indexer(5, 'sequential')
    assert [next(i) for _ in range(10)] == list(range(5)) * 2

def test_no_seed_different_each_time():
    i = Indexer(1e6)
    a = [next(i) for _ in range(10)]
    b = list(range(10))
    assert a != b
    assert len(set(a)) == 10

def test_reproducible_indexing():
    i = Indexer(1e6, seed=12345)
    a = [next(i) for _ in range(10)]
    i = Indexer(1e6, seed=12345)
    b = [next(i) for _ in range(10)]
    assert a == b
    assert a != list(range(10))

def test_sequential_seed():
    i = Indexer(1e6, seed='sequential')
    a = [next(i) for _ in range(10)]
    assert a == list(range(10))
    assert i.count == 10
    assert i.index == 9

def test_count():
    i = Indexer(1e6)
    for index in range(10):
        assert i.count == index
        next(i)

def test_index_attribute():
    i = Indexer(1e6)
    assert i.index is None
    for index in range(10):
        next(i)
        assert i.index != i.count

def test_sequential_reset():
    i = Indexer(1e6, seed='sequential')
    a = [next(i) for _ in range(10)]
    assert a == list(range(10))
    assert i.count == 10
    assert i.index == 9

    i.reset_sequential_indices()
    assert i.count == i.index == 0

    a = [next(i) for _ in range(10)]
    assert a == list(range(10))
    assert i.count == 10
    assert i.index == 9

