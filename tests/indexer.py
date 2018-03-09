from presamples import Indexer
from pathlib import Path
from scipy.sparse import *
import numpy as np
import pytest
import tempfile


def test_seed():
    i = Indexer()
    assert i.seed_value is None
    i = Indexer(seed=42)
    assert i.seed_value == 42

def test_ncols():
    i = Indexer()
    assert i.ncols == 0
    i = Indexer(42)
    assert i.ncols == 42

def test_no_seed_different_each_time():
    i = Indexer()
    a = [next(i) for _ in range(10)]
    b = list(range(10))
    assert a != b
    assert len(set(a)) == 10

def test_reproducible_indexing():
    i = Indexer(seed=12345)
    a = [next(i) for _ in range(10)]
    i = Indexer(seed=12345)
    b = [next(i) for _ in range(10)]
    assert a == b
    assert a != list(range(10))

def test_sequential_seed():
    i = Indexer(seed='sequential')
    a = [next(i) for _ in range(10)]
    assert a == list(range(10))
    assert i.count == 10
    assert i.index == 9

def test_count():
    i = Indexer()
    for index in range(10):
        assert i.count == index
        next(i)

def test_index_attribute():
    i = Indexer()
    assert i.index is None
    for index in range(10):
        next(i)
        assert i.index != i.count
