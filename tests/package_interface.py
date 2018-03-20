from presamples import create_presamples_package, Indexer
from presamples.package_interface import *
import numpy as np
import pytest
import tempfile


@pytest.fixture
def parameters_package():
    with tempfile.TemporaryDirectory() as d:
        dirpath = Path(d)
        s1 = np.arange(16, dtype=np.int64).reshape((4, 4))
        s2 = np.arange(12, dtype=np.int64).reshape((3, 4))
        n1 = list('ABCD')
        n2 = list('EFG')
        id_, dirpath = create_presamples_package(
            parameter_data=[(s1, n1, 'winter'), (s2, n2, 'summer')],
            name='foo', id_='bar', dirpath=dirpath, seed=42
        )
        yield dirpath


def test_basic_presamplespackage(parameters_package):
    pp = PresamplesPackage(parameters_package)
    assert isinstance(pp.metadata, dict)
    assert pp.name == 'foo'
    assert pp.seed == 42
    assert pp.id == 'bar'
    assert isinstance(pp.resources, list)
    assert len(pp.resources) == 2
    assert len(pp) == 2

def test_indexer(parameters_package):
    pp = PresamplesPackage(parameters_package)
    assert isinstance(pp.indexer, Indexer)
    assert pp.indexer.index is not None
    first = pp.indexer.index
    next(pp.indexer)
    assert first != pp.indexer.index
    assert first is not pp.indexer.index

def test_change_seed(parameters_package):
    pp = PresamplesPackage(parameters_package)
    pp.change_seed(88)
    new = PresamplesPackage(parameters_package)
    assert pp.seed == 88

def test_parameters(parameters_package):
    p = PresamplesPackage(parameters_package).parameters
    assert len(p) == 7
    assert np.allclose(p['A'], range(4))
    assert np.allclose(p['D'], range(12, 16))
    assert np.allclose(p['E'], range(4))
    assert np.allclose(p['G'], range(8, 12))
    assert not hasattr(p, "index")
    expected = [
        (parameters_package, 'foo', o)
        for o in 'ABCDEFG'
    ]
    assert p.ids == expected
    expected = {
        'A': (0, 0),
        'B': (0, 1),
        'C': (0, 2),
        'D': (0, 3),
        'E': (1, 0),
        'F': (1, 1),
        'G': (1, 2)
    }
    assert p.mapping == expected
    assert 'E' in p
    assert list(iter(p)) == list('ABCDEFG')

def test_parameters_values(parameters_package):
    p = PresamplesPackage(parameters_package).parameters
    possibles = [6, 22, 38, 54]
    for row in p.values():
        assert isinstance(row, np.ndarray)
        assert row.shape == (4,)
        assert row.sum() in possibles

def test_indexed_parameter_mapping_without_indexer(parameters_package):
    pp = PresamplesPackage(parameters_package)
    p = IndexedParametersMapping(pp.path, pp.resources, pp.name)
    assert p.index == 0
    p.index = 6
    assert p.index == 6

def test_indexed_parameter_mapping_values(parameters_package):
    pp = PresamplesPackage(parameters_package)
    p = IndexedParametersMapping(pp.path, pp.resources, pp.name)
    possibles  = [0, 4, 8, 12]
    for value in p.values():
        assert isinstance(value, float)
        assert value in possibles

def test_indexed_parameter_array(parameters_package):
    pp = PresamplesPackage(parameters_package)
    p = IndexedParametersMapping(pp.path, pp.resources, pp.name)
    assert np.allclose(np.array([0, 4, 8, 12, 0, 4, 8]), p.array)
