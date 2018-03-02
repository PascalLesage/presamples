import numpy as np
import pytest

from bw_presamples.models.inventory_base import InventoryBaseModel
from bw_presamples import PackagesDataLoader
try:
    from bw2data.tests import bw2test
    from bw2data import Database
except ImportError:
    bw2test = pytest.mark.skip


@pytest.fixture
@bw2test
def db():
    bio_data =  {
        ("bio", "a"): {'exchange': [], 'type': 'biosphere'},
        ("bio", "b"): {'exchange': [], 'type': 'biosphere'},
    }
    Database("bio").write(bio_data)

    tech_data =  {("test", "1"): {
        'exchanges': [{
            'amount': 1,
            'type': 'production',
            'input': ("test", "1"),
            'uncertainty type': 0
        }, {
            'amount': 0.1,
            'type': 'technosphere',
            'input': ("test", "3"),
            'uncertainty type': 0
        }, {
            'amount': 7,
            'type': 'biosphere',
            'input': ("bio", "b"),
            'uncertainty type': 0
        }],
    },
    ("test", "2"): {
        'exchanges': [{
            'amount': 0.5,
            'type': 'production',
            'input': ("test", "2"),
            'uncertainty type': 0
        }, {
            'amount': -2,
            'type': 'technosphere',
            'input': ("test", "1"),
            'uncertainty type': 0
        }, {
            'amount': 1,
            'type': 'biosphere',
            'input': ("bio", "a"),
            'uncertainty type': 0
        }, {
            'amount': 5,
            'type': 'biosphere',
            'input': ("bio", "b"),
            'uncertainty type': 0
        }],
    },
    ("test", "3"): {
        'exchanges': [{
            'amount': 1,
            'type': 'production',
            'input': ("test", "3"),
            'uncertainty type': 0
        }, {
            'amount': 0.1,
            'type': 'technosphere',
            'input': ("test", "3"),
            'uncertainty type': 0
        }, {
            'amount': 3,
            'type': 'technosphere',
            'input': ("test", "1"),
            'uncertainty type': 0
        }, {
            'amount': 2,
            'type': 'technosphere',
            'input': ("test", "2"),
            'uncertainty type': 0
        }, {
            'amount': 22,
            'type': 'biosphere',
            'input': ("bio", "a"),
            'uncertainty type': 0
        }],
    }}

    Database("test").write(tech_data)

def test_find_exchanges_multiple_error(db):
    im = InventoryBaseModel()
    with pytest.raises(ValueError):
        im.find_exchanges([(('test', '3'), ('test', '3'))])

def test_find_exchanges_two_tuple(db):
    im = InventoryBaseModel()
    result = im.find_exchanges([
        (('test', '2'), ('test', '3')),
        (('bio', 'a'), ('test', '3')),
    ])
    expected = [
        {'amount': 2, 'type': 'technosphere', 'input': ('test', '2'),
         'uncertainty type': 0, 'output': ('test', '3')},
        {'amount': 22, 'type': 'biosphere', 'input': ('bio', 'a'),
         'uncertainty type': 0, 'output': ('test', '3')}
    ]
    assert result == expected

def test_find_exchanges_three_tuple(db):
    im = InventoryBaseModel()
    result = im.find_exchanges([
        (('test', '2'), ('test', '3'), 'technosphere'),
        (('bio', 'a'), ('test', '3'), 'biosphere'),
    ])
    expected = [
        {'amount': 2, 'type': 'technosphere', 'input': ('test', '2'),
         'uncertainty type': 0, 'output': ('test', '3')},
        {'amount': 22, 'type': 'biosphere', 'input': ('bio', 'a'),
         'uncertainty type': 0, 'output': ('test', '3')}
    ]
    assert result == expected

def test_find_exchanges_exchange_object(db):
    a = Database("test").get("3")
    exchanges = []
    for exc in a.technosphere():
        if exc.input.key == ('test', '2'):
            exchanges.append(exc)
    for exc in a.biosphere():
        if exc.input.key == ('bio', 'a'):
            exchanges.append(exc)
    im = InventoryBaseModel()
    result = im.find_exchanges(exchanges)
    expected = [
        {'amount': 2, 'type': 'technosphere', 'input': ('test', '2'),
         'uncertainty type': 0, 'output': ('test', '3')},
        {'amount': 22, 'type': 'biosphere', 'input': ('bio', 'a'),
         'uncertainty type': 0, 'output': ('test', '3')}
    ]
    assert result == expected

@bw2test
def test_presample_creation():
    exchanges = [
        {'input': 0, 'output': 1, 'type': 'technosphere'},
        {'input': 2, 'output': 3, 'type': 'production'},
        {'input': 4, 'output': 5, 'type': 'biosphere'},
        {'input': 6, 'output': 7, 'type': 'biosphere'},
    ]
    model = InventoryBaseModel()
    model.data = exchanges
    model.matrix_array =  np.arange(20).reshape((4, 5))
    package = model.create_stored_presample_package("test")
    assert package.id == 1
    assert package.name == "test"
    assert package.description is None
    print(package.path)
    mp = PackagesDataLoader([package.path])
    assert len(mp.data) == 1
    assert mp.data[0]['name'] == 'test'
    assert 'id' in mp.data[0]
    b, t = mp.data[0]['matrix-data']
    assert b['matrix'] == 'biosphere_matrix'
    assert t['matrix'] == 'technosphere_matrix'
    assert b['samples'].data[0][0].shape == (2, 5)
    assert t['samples'].data[0][0].shape == (2, 5)
