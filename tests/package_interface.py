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
    assert p['A'] in range(4)
    assert p['D'] in range(12, 16)
    assert p['E'] in range(4)
    assert p['G'] in range(8, 12)
    assert isinstance(p.index, int)
    print(p.ids)
    expected = [
        (parameters_package, 'foo', o)
        for o in 'ABCDEFG'
    ]
    assert p.ids == expected
    expected = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 0, 'F': 1, 'G': 2}
    assert p.mapping == expected
    assert 'E' in p
    assert list(iter(p)) == list('ABCDEFG')

def test_parameters_get_updated_index(parameters_package):
    pp = PresamplesPackage(parameters_package)
    ps = pp.parameters
    first = pp.indexer.index
    assert ps.index == first
    next(pp.indexer)
    assert ps.index != first
    assert ps.index == pp.indexer.index

def test_manual_index(parameters_package):
    pp = PresamplesPackage(parameters_package)
    pm = ParametersMapping(
        parameters_package,
        pp.resources,
        'foo',
        1
    )
    assert np.allclose(pm.values(), [1, 5 , 9, 13, 1, 5, 9])

def test_set_manual_index(parameters_package):
    p = PresamplesPackage(parameters_package).parameters
    p.index = 2
    assert p.index == 2
    assert np.allclose(p.values(), [2, 6 , 10, 14, 2, 6, 10])
