import numpy as np
import pytest

from bw_presamples.models.inventory_base import InventoryBaseModel
from bw_presamples import MatrixPresamples
try:
    from bw2data.tests import bw2test
    from bw2data import Database, mapping
except ImportError:
    bw2test = pytest.mark.skip

@pytest.fixture
@bw2test
def db():
    data = None
    db = Database("test")
    db.write(data)
    return db

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
    mp = MatrixPresamples([package.path])
    assert len(mp.data) == 1
    assert mp.data[0]['name'] == 'test'
    assert 'id' in mp.data[0]
    b, t = mp.data[0]['resources']
    assert b['matrix'] == 'biosphere_matrix'
    assert t['matrix'] == 'technosphere_matrix'
    assert b['samples'].data[0][0].shape == (2, 5)
    assert t['samples'].data[0][0].shape == (2, 5)
