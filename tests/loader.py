from pathlib import Path
from scipy.sparse import dok_matrix
import json
import numpy as np
import os
import pytest
import tempfile

from presamples import *
from presamples.errors import *
try:
    from bw2data import mapping
    from bw2data.tests import bw2test
except ImportError:
    bw2test = pytest.mark.skip


class MockLCA:
    def __init__(self):
        self.matrix = dok_matrix((5, 5))
        for i in range(5):
             for j in range(5):
                 self.matrix[i, j] = 0
        self.row_dict = {x: 2 * x for x in range(5)}
        self.col_dict = {x: 3 * x for x in range(5)}


@pytest.fixture
def tempdir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

@pytest.fixture
@bw2test
def package():
    a = np.ones(shape=(3, 4)) * 100
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'matrix'
    }
    frmt = lambda x: (x[0], x[1], x[0], x[1])
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    id_, dirpath = create_presamples_package(
        [(a, b, 'mock', dtype, frmt, metadata)],
    )
    return dirpath

@pytest.fixture
def parameters_fixture():
    with tempfile.TemporaryDirectory() as d:
        dirpath = Path(d)
        s1 = np.arange(16, dtype=np.int64).reshape((4, 4))
        s2 = np.arange(12, dtype=np.int64).reshape((3, 4))
        n1 = list('ABCD')
        n2 = list('EFG')
        id_, dirpath = create_presamples_package(
            parameter_data=[(s1, n1, 'winter'), (s2, n2, 'summer')],
            name='foo', id_='bar', dirpath=dirpath
        )
        yield dirpath

@pytest.fixture
def parameters_fixture_2():
    with tempfile.TemporaryDirectory() as d:
        dirpath = Path(d)
        s1 = np.array([100, 200]).reshape(2, 1)
        s2 = np.array([42]).reshape(1, 1)
        n1 = list('AB')
        n2 = list('E')
        id_, dirpath = create_presamples_package(
            parameter_data=[(s1, n1, 'spring'), (s2, n2, 'fall')],
            name='nufoo', id_='nubar', dirpath=dirpath
        )
        yield dirpath

@pytest.fixture
def parameters_fixture_3():
    with tempfile.TemporaryDirectory() as d:
        dirpath = Path(d)
        s1 = np.array([300]).reshape(1, 1)
        s2 = np.array([123]).reshape(1, 1)
        n1 = list('C')
        n2 = list('E')
        id_, dirpath = create_presamples_package(
            parameter_data=[(s1, n1, 'equinox'), (s2, n2, 'solstice')],
            name='nunufoo', id_='nunubar', dirpath=dirpath
        )
        yield dirpath


def test_init(package):
    mp = PackagesDataLoader([package])
    assert not mp.empty
    assert len(mp.matrix_data_loaded) == 1
    assert 'id' in mp.matrix_data_loaded[0]
    assert 'name' in mp.matrix_data_loaded[0]
    assert len(mp.matrix_data_loaded[0]['matrix-data']) == 1
    resources = mp.matrix_data_loaded[0]['matrix-data'][0]
    assert resources['type'] == 'mock'
    assert resources['matrix'] == 'matrix'
    for key in ('row from label', 'row to label', 'row dict',
                'col from label', 'col to label', 'col dict'):
        assert key in resources
    assert isinstance(resources['samples'], RegularPresamplesArrays)
    assert isinstance(resources['indices'], np.ndarray)

def test_str(package):
    mp = PackagesDataLoader([package])
    assert "PackagesDataLoader with 1 packages" in str(mp)

def test_len(package):
    mp = PackagesDataLoader([package])
    assert len(mp) == 1

def test_update_matrices(package):
    mp = PackagesDataLoader([package])
    lca = MockLCA()
    mp.update_matrices(lca)
    assert lca.matrix[1, 1] == 100
    assert lca.matrix[1, 2] == 100
    assert lca.matrix[2, 3] == 100
    assert lca.matrix.sum() == 300

def test_update_matrices_no_lca(package):
    mp = PackagesDataLoader([package])
    with pytest.raises(ValueError):
        mp.update_matrices()

def test_update_matrices_lca_init_arg(package):
    lca = MockLCA()
    mp = PackagesDataLoader([package], lca=lca)
    mp.update_matrices()
    assert lca.matrix[1, 1] == 100
    assert lca.matrix[1, 2] == 100
    assert lca.matrix[2, 3] == 100
    assert lca.matrix.sum() == 300

def test_update_matrices_skip_missing_matrix(package):
    class WrongLCA:
        def __init__(self):
            self.wrong = dok_matrix((5, 5))
            for i in range(5):
                 for j in range(5):
                     self.wrong[i, j] = 0
            self.row_dict = {x: 2 * x for x in range(5)}
            self.col_dict = {x: 3 * x for x in range(5)}

    mp = PackagesDataLoader([package])
    lca = WrongLCA()
    mp.update_matrices(lca)
    assert not lca.wrong.sum()

@bw2test
def test_update_matrices_technosphere():
    mapping.add('ABCDEF')
    for x, y in enumerate('ABCDEF'):
        assert mapping[y] == x + 1

    # 0 is production, 3 is substitution
    t1 = [
        ('A', 'A', 0),
        ('A', 'B', 1),
        ('B', 'C', 3),
        ('C', 'D', 1),
        ('C', 'D', 1)
        ]
    t2 = np.arange(5).reshape((5, 1)) + 10
    _, dirpath = create_presamples_package([(t2, t1, 'technosphere')])

    class LCA:
        def __init__(self):
            self.technosphere_matrix = dok_matrix((5, 5))
            for i in range(5):
                 for j in range(5):
                     self.technosphere_matrix[i, j] = 0
            self._activity_dict = {x: x-1 for x in range(1, 7)}
            self._product_dict = self._activity_dict

    lca = LCA()
    mp = PackagesDataLoader([dirpath])
    mp.index_arrays(lca)
    mp.update_matrices(lca)
    assert lca.technosphere_matrix[0, 0] == 10
    assert lca.technosphere_matrix[0, 1] == -11
    assert lca.technosphere_matrix[1, 2] == 12
    assert lca.technosphere_matrix[2, 3] == -14
    assert lca.technosphere_matrix.sum() == 10 - 11 + 12 - 14
    
@bw2test
def test_update_matrices_one_dimensional():
    mapping.add('ABCDEF')
    for x, y in enumerate('ABCDEF'):
        assert mapping[y] == x + 1

    # 0 is production, 3 is substitution
    t1 = list('ACD')
    t2 = np.arange(3).reshape((3, 1)) + 10
    _, dirpath = create_presamples_package([(t2, t1, 'cf')])

    class LCA:
        def __init__(self):
            self.characterization_matrix = dok_matrix((5, 5))
            for i in range(5):
                 for j in range(5):
                     self.characterization_matrix[i, j] = 0
            self._biosphere_dict = {x: x-1 for x in range(1, 7)}

    lca = LCA()
    mp = PackagesDataLoader([dirpath])
    mp.index_arrays(lca)
    mp.update_matrices(lca)
    assert lca.characterization_matrix[0, 0] == 10
    assert lca.characterization_matrix[2, 2] == 11
    assert lca.characterization_matrix[3, 3] == 12
    assert lca.characterization_matrix.sum() == 10 + 11 + 12

def test_index_arrays(package):
    mp = PackagesDataLoader([package])
    lca = MockLCA()
    assert 'indexed' not in mp.matrix_data_loaded[0]['matrix-data'][0]
    mp.index_arrays(lca)
    expected = [(1, 1, 2, 3), (1, 2, 2, 6), (2, 3, 4, 9)]
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indices'].tolist() == expected
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indexed']

def test_index_arrays_already_indexed(package):
    mp = PackagesDataLoader([package])
    lca = MockLCA()
    assert 'indexed' not in mp.matrix_data_loaded[0]['matrix-data'][0]
    expected = [(1, 1, 1, 1), (1, 2, 1, 2), (2, 3, 2, 3)]
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indices'].tolist() == expected
    mp.index_arrays(lca)
    expected = [(1, 1, 2, 3), (1, 2, 2, 6), (2, 3, 4, 9)]
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indices'].tolist() == expected
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indexed']
    lca.row_dict = {x: 0 for x in range(5)}
    lca.col_dict = {x: 0 for x in range(5)}
    mp.index_arrays(lca)
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indices'].tolist() == expected

def test_index_arrays_missing_row_dict(package):
    mp = PackagesDataLoader([package])
    lca = MockLCA()
    del lca.row_dict
    expected = [(1, 1, 1, 1), (1, 2, 1, 2), (2, 3, 2, 3)]
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indices'].tolist() == expected
    mp.index_arrays(lca)

def test_start_with_indexer_advanced(package):
    mp = PackagesDataLoader([package])
    assert mp.package_indexers[0].index is not None

def test_index_arrays_missing_col_dict(package):
    mp = PackagesDataLoader([package])
    lca = MockLCA()
    del lca.col_dict
    expected = [(1, 1, 1, 1), (1, 2, 1, 2), (2, 3, 2, 3)]
    assert mp.matrix_data_loaded[0]['matrix-data'][0]['indices'].tolist() == expected
    mp.index_arrays(lca)

def test_functionality_with_empty(tempdir):
    datapackage = {
        "name": "foo",
        "id": "one",
        "seed": None,
        "profile": "data-package",
        "resources": [],
        "ncols": None,
    }
    with open(tempdir / "datapackage.json", "w", encoding='utf-8') as f:
        json.dump(datapackage, f)
    mp = PackagesDataLoader([tempdir])
    assert mp.empty
    mp.index_arrays(None)
    mp.update_matrices(None)

def test_validate_dirpath_missing_datapackage(package):
    os.unlink(package / "datapackage.json")
    with pytest.raises(AssertionError):
        PackagesDataLoader([package])

def test_validate_dirpath_missing_samples(package):
    for fp in os.listdir(package):
        if "samples.npy" in fp:
            os.unlink(package / fp)
    with pytest.raises(AssertionError):
        PackagesDataLoader([package])

def test_validate_dirpath_altered_samples(package):
    for fp in os.listdir(package):
        if "samples.npy" in fp:
            with open(package / fp, "w") as f:
                f.write("woops")
    with pytest.raises(AssertionError):
        PackagesDataLoader([package])

def test_validate_dirpath_missing_indices(package):
    for fp in os.listdir(package):
        if "indices.npy" in fp:
            os.unlink(package / fp)
    with pytest.raises(AssertionError):
        PackagesDataLoader([package])

def test_validate_dirpath_altered_indices(package):
    for fp in os.listdir(package):
        if "indices.npy" in fp:
            with open(package / fp, "w") as f:
                f.write("woops")
    with pytest.raises(AssertionError):
        PackagesDataLoader([package])

@bw2test
def test_seed_functions():
    a = np.arange(12).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'matrix'
    }
    frmt = lambda x: (x[0], x[1], x[0], x[1])
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    _, dirpath = create_presamples_package(
        [(a, b, 'mock', dtype, frmt, metadata)],
    )
    mp = PackagesDataLoader([dirpath], 987654321)
    sampler = mp.matrix_data_loaded[0]['matrix-data'][0]['samples']
    indexer = mp.package_indexers[0]
    assert indexer.index is not None
    first = [sampler.sample(next(indexer)).sum() for _ in range(100)]
    mp = PackagesDataLoader([dirpath], 987654321)
    sampler = mp.matrix_data_loaded[0]['matrix-data'][0]['samples']
    indexer = mp.package_indexers[0]
    second = [sampler.sample(next(indexer)).sum() for _ in range(100)]
    assert first == second

    mp = PackagesDataLoader([dirpath], 12345)
    sampler = mp.matrix_data_loaded[0]['matrix-data'][0]['samples']
    indexer = mp.package_indexers[0]
    third = [sampler.sample(next(indexer)).sum() for _ in range(100)]
    assert first != third


@pytest.fixture
def mp():
    class Mock(PackagesDataLoader):
        def __init__(self):
            pass

    return Mock()

@pytest.fixture
def mock_ipa(monkeypatch):
    class FakeRPA:
        def __init__(self, one, two=None):
            self.one = one
            self.two = two

    monkeypatch.setattr(
        'presamples.loader.RegularPresamplesArrays',
        FakeRPA
    )

def test_consolidate_mismatched_matrices(package, mp):
    group = [{'matrix': 'a'}, {'matrix': 'b'}]
    with pytest.raises(AssertionError):
        mp.consolidate(package, group)

def test_consolidate_conficting_row_labels(mp):
    data = [
        {
            'row from label': 'f1',
            'row to label': 'f3',
            'row dict': 'row_dict',
            'col from label': 'f1',
            'col to label': 'f3',
            'col dict': 'col_dict',
            'matrix': 'm'
        }, {
            'row from label': 'f1',
            'row to label': 'f3',
            'row dict': 'row_dict',
            'col from label': '1f',
            'col to label': 'f3',
            'col dict': 'col_dict',
            'matrix': 'm'
        }
    ]
    with pytest.raises(ConflictingLabels):
        mp.consolidate(None, data)

def test_consolidate_conflicting_col_labels(mp):
    data = [
        {
            'row from label': 'f1',
            'row to label': 'f3',
            'row dict': 'row_dict',
            'matrix': 'm'
        }, {
            'row from label': '1f',
            'row to label': 'f3',
            'row dict': 'row_dict',
            'matrix': 'm'
        }
    ]
    with pytest.raises(ConflictingLabels):
        mp.consolidate(None, data)

def test_consolidate_conflicting_indices(mp, tempdir):
    a = np.ones(shape=(3, 4)) * 100
    b = [(1, 1), (1, 2), (2, 3)]
    c = np.ones(shape=(2, 4)) * 200
    d = [(10, 11), (12, 13)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'matrix'
    }
    frmt = lambda x: (x[0], x[1], x[0], x[1])
    dtype_one = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    dtype_two = [
        ('f1', np.int64),
        ('f2', np.int64),
        ('f3', np.int64),
        ('f4', np.int64),
    ]
    id_, dirpath = create_presamples_package([
            (a, b, 'mock', dtype_one, frmt, metadata),
            (c, d, 'mock', dtype_two, frmt, metadata),
        ], dirpath=tempdir
    )
    with pytest.raises(IncompatibleIndices):
        mp.consolidate(
            dirpath,
            PresamplesPackage(dirpath).metadata['resources']
        )

def test_consolidate_single_group(mock_ipa, mp, tempdir):
    a = np.ones(shape=(3, 4)) * 100
    b = [(1, 1), (1, 2), (2, 3)]

    c = np.ones(shape=(2, 4)) * 200
    d = [(10, 11), (12, 13)]

    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'matrix'
    }
    frmt = lambda x: (x[0], x[1], x[0], x[1])
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    id_, dirpath = create_presamples_package([
            (a, b, 'mock', dtype, frmt, metadata),
            (c, d, 'mock', dtype, frmt, metadata),
        ], dirpath=tempdir
    )

    expected = [
        f'{id_}.0.samples.npy',
        f'{id_}.0.indices.npy',
        f'{id_}.1.samples.npy',
        f'{id_}.1.indices.npy',
        'datapackage.json'
    ]
    assert sorted(os.listdir(dirpath)) == sorted(expected)

    results = mp.consolidate(dirpath, PresamplesPackage(dirpath).metadata['resources'])
    expected = [
        dirpath / f'{id_}.0.samples.npy',
        dirpath / f'{id_}.1.samples.npy',
    ]
    rpa = results['samples']
    assert rpa.one == expected
    assert rpa.two is None

def test_consolidate_multiple_groups(mock_ipa, tempdir):
    a = np.ones(shape=(4, 4)) * 100
    b = [(1, 1), (1, 2), (2, 3), (4, 5)]
    c = np.ones(shape=(3, 4)) * 200
    d = [(21, 21), (21, 22), (22, 23)]
    e = np.ones(shape=(2, 4)) * 300
    f = [(10, 11), (12, 13)]
    g = np.ones(shape=(1, 4)) * 400
    h = [(30, 31)]
    metadata_one = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'rude'
    }
    metadata_two = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'row_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'col_dict',
        'matrix': 'polite'
    }
    frmt = lambda x: (x[0], x[1], x[0], x[1])
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    id_one, dirpath_one = create_presamples_package([
            (a, b, 'mock', dtype, frmt, metadata_one),
            (e, f, 'mock', dtype, frmt, metadata_one),
        ], dirpath=tempdir
    )
    id_two, dirpath_two = create_presamples_package([
            (c, d, 'mock', dtype, frmt, metadata_two),
            (g, h, 'mock', dtype, frmt, metadata_two),
        ], dirpath=tempdir
    )

    mp = PackagesDataLoader([dirpath_one, dirpath_two])
    expected = np.array([
        ( 1,  1,  1,  1),
        ( 1,  2,  1,  2),
        ( 2,  3,  2,  3),
        ( 4,  5,  4,  5),
        (10, 11, 10, 11),
        (12, 13, 12, 13)
    ])
    for x, y in zip(mp.matrix_data_loaded[0]['matrix-data'][0]['indices'], expected):
        assert np.allclose(list(x), y)

    expected = np.array([
        (21, 21, 21, 21),
        (21, 22, 21, 22),
        (22, 23, 22, 23),
        (30, 31, 30, 31),
    ])
    for x, y in zip(mp.matrix_data_loaded[1]['matrix-data'][0]['indices'], expected):
        assert np.allclose(list(x), y)

    assert mp.matrix_data_loaded[0]['matrix-data'][0]['samples'].two is None
    assert '0.samples.npy' in str(mp.matrix_data_loaded[0]['matrix-data'][0]['samples'].one[0])
    assert '1.samples.npy' in str(mp.matrix_data_loaded[0]['matrix-data'][0]['samples'].one[1])
    assert mp.matrix_data_loaded[1]['matrix-data'][0]['samples'].two is None
    assert '0.samples.npy' in str(mp.matrix_data_loaded[1]['matrix-data'][0]['samples'].one[0])
    assert '1.samples.npy' in str(mp.matrix_data_loaded[1]['matrix-data'][0]['samples'].one[1])

def test_accepts_campaign_as_input(package, parameters_fixture):
    pr1 = PresampleResource.create(name='one', path=package)
    pr2 = PresampleResource.create(name='two', path=parameters_fixture)
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr2)
    mp = PackagesDataLoader(c)
    assert len(mp) == 2
    assert len(mp.parameter_data_loaded) == 1
    assert len(mp.matrix_data_loaded) == 1

def test_parameters_package(package, parameters_fixture):
    mp = PackagesDataLoader([package, parameters_fixture])
    assert len(mp) == 2
    assert len(mp.parameter_data_loaded) == 1
    assert len(mp.matrix_data_loaded) == 1
    assert "PackagesDataLoader with 2 packages" in str(mp)
    assert mp.parameters['E'] in range(4)

def test_update_package_indices():
    class MockLoader(PackagesDataLoader):
        def __init__(self):
            self.package_indexers = [Indexer(12345)]

    ml = MockLoader()
    assert len(ml.package_indexers) == 1
    assert ml.package_indexers[0].index is None

    ml.update_package_indices()
    first = ml.package_indexers[0].index
    ml.update_package_indices()
    assert ml.package_indexers[0].index != first

def test_no_parameters_in_matrix_data(package, parameters_fixture):
    mp = PackagesDataLoader([package, parameters_fixture])
    assert mp.matrix_data_loaded[0].get('parameter-metadata', None) is None
    assert mp.parameter_data_loaded[0].get('matrix-data', None) is None

def test_consolidated_indexed_parameter_arrays(parameters_fixture, parameters_fixture_2, parameters_fixture_3):
    mp_1 = PackagesDataLoader([parameters_fixture])
    assert len(mp_1.parameter_data_loaded) == 1
    assert len(mp_1.parameters) == 7
    assert mp_1.parameters.names == list("ABCDEFG")
    itered_names = [n for n in mp_1.parameters]
    assert itered_names == list("ABCDEFG")
    # Consolidated array depends on index, but is sure to be one of following:
    first_col_arr = np.array([0, 4, 8, 12, 0, 4, 8], dtype=np.float)
    possible_consolidated_arrays = [first_col_arr+scalar for scalar in range(0, 4)]
    assert any([np.array_equal(mp_1.parameters.consolidated_array, arr) for arr in possible_consolidated_arrays])
    assert len(set(mp_1.parameters.consolidated_indices))==1
    # Values still possible after updating index
    mp_1.update_package_indices()
    assert any([np.array_equal(mp_1.parameters.consolidated_array, arr) for arr in possible_consolidated_arrays])
    assert len(set(mp_1.parameters.consolidated_indices)) == 1
    # All parameter values taken from ipm at index 0
    assert all([mp_1.parameters.ipm_mapper[n] == 0 for n in mp_1.parameters.names])
    assert len(mp_1.parameters.replaced) == 0
    all_ids_paths = [mp_1.parameters.ids[name][0] for name in mp_1.parameters.names]
    assert all([Path(p) == Path(parameters_fixture) for p in all_ids_paths]), "Got {}, expected {}".format(all_ids_paths, parameters_fixture)

    mp_2 = PackagesDataLoader([parameters_fixture, parameters_fixture_2])
    assert len(mp_2.parameter_data_loaded) == 2
    assert len(mp_2.parameters) == 7
    assert mp_2.parameters.names == list("ABCDEFG")
    # Consolidated array depends on index, but is sure to be one of following:
    not_replaced_first_col = np.array([8, 12, 4, 8], dtype=np.float)
    possible_not_replaced_sample = [not_replaced_first_col+scalar for scalar in range(0, 4)]
    not_replaced_indices = [2, 3, 5, 6]
    replaced_indices = [0, 1, 4]
    # Unreplaced named parameters still in possible values
    assert any([np.array_equal(mp_2.parameters.consolidated_array[not_replaced_indices], arr) for arr in possible_not_replaced_sample]), "got this: {}".format(mp_1.parameters.consolidated_array)
    # Replaced named parameters have new values
    assert np.array_equal(mp_2.parameters.consolidated_array[replaced_indices], np.array([100, 200, 42]))
    # All replaced names have index values == 0 (since the number of observations == 1)
    assert all([mp_2.parameters.consolidated_indices[i]==0 for i in [0, 1, 4]])
    # All unreplaced names have same index, since have the same indexer
    assert len(set([mp_2.parameters.consolidated_indices[i] for i in [2, 3, 5, 6]]))

    # Value tests still correct after updating index
    mp_2.update_package_indices()
    assert any([np.array_equal(mp_2.parameters.consolidated_array[not_replaced_indices], arr) for arr in possible_not_replaced_sample])
    assert np.array_equal(mp_2.parameters.consolidated_array[replaced_indices], np.array([100, 200, 42]))

    # All parameter values taken from imp at index 0
    assert all(
        [mp_2.parameters.ipm_mapper[n] == 0
         for n in mp_2.parameters.names
         if n not in mp_2.parameters.replaced.keys()
         ]
    )
    assert all(
        [mp_2.parameters.ipm_mapper[n] == 1
         for n in mp_2.parameters.names
         if n in mp_2.parameters.replaced.keys()
         ]
    )

    assert len(mp_2.parameters.replaced) == 3
    for replaced_name, replaced_paths in mp_2.parameters.replaced.items():
        assert len(replaced_paths)==1
        assert replaced_paths==[(parameters_fixture, 'foo')]

    all_ids_paths_not_replaced = [
        mp_2.parameters.ids[name][0]
        for name in mp_2.parameters.names
        if name not in mp_2.parameters.replaced
    ]
    all_ids_paths_replaced = [
        mp_2.parameters.ids[name][0]
        for name in mp_2.parameters.names
        if name in mp_2.parameters.replaced
    ]
    assert all([
        Path(p) == Path(parameters_fixture) for p in all_ids_paths_not_replaced
        ]
    )
    assert all([
        Path(p) == Path(parameters_fixture_2) for p in all_ids_paths_replaced
        ]
    )

    mp_3 = PackagesDataLoader([parameters_fixture, parameters_fixture_2, parameters_fixture_3])
    assert len(mp_3.parameter_data_loaded) == 3
    assert len(mp_3.parameters) == 7
    assert mp_2.parameters.names == list("ABCDEFG")
    # Consolidated array depends on index, but is sure to be one of following:
    not_replaced_first_col = np.array([12, 4, 8], dtype=np.float)
    possible_not_replaced_sample = [not_replaced_first_col + scalar for scalar in range(0, 4)]
    not_replaced_indices = [3, 5, 6]
    replaced_indices = [0, 1, 2, 4]
    # Unreplaced named parameters still in possible values
    assert any([
        np.array_equal(mp_3.parameters.consolidated_array[not_replaced_indices], arr)
        for arr in possible_not_replaced_sample
    ])
    # Replaced named parameters have new values
    assert np.array_equal(mp_3.parameters.consolidated_array[replaced_indices], np.array([100, 200, 300, 123]))
    # Value tests still correct after updating index
    mp_3.update_package_indices()
    assert any([np.array_equal(mp_3.parameters.consolidated_array[not_replaced_indices], arr) for arr in
                possible_not_replaced_sample])
    assert np.array_equal(mp_3.parameters.consolidated_array[replaced_indices], np.array([100, 200, 300, 123]))

    # All parameter values taken from imp at index 0
    assert all(
        [mp_3.parameters.ipm_mapper[n] == 0
         for n in mp_3.parameters.names
         if n not in mp_3.parameters.replaced.keys()
         ]
    )
    assert all(
        [mp_3.parameters.ipm_mapper[n] == 1
         for n in mp_3.parameters.names
         if n in list('AB')
         ]
    )
    assert all(
        [mp_3.parameters.ipm_mapper[n] == 2
         for n in mp_3.parameters.names
         if n in list('CE')
         ]
    )

    assert len(mp_3.parameters.replaced) == 4
    assert mp_3.parameters.replaced['A'] == [(parameters_fixture, 'foo')]
    assert mp_3.parameters.replaced['B'] == [(parameters_fixture, 'foo')]
    assert mp_3.parameters.replaced['C'] == [(parameters_fixture, 'foo')]
    assert mp_3.parameters.replaced['E'] == [(parameters_fixture, 'foo'), (parameters_fixture_2, 'nufoo')]
