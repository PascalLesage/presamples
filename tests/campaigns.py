from pathlib import Path
from peewee import DoesNotExist
import copy
import datetime
import numpy as np
import pytest
import tempfile
import time

from bw_presamples import create_presamples_package
from bw_presamples.campaigns import *
from bw_presamples.errors import MissingPresample
try:
    from bw2data.tests import bw2test
except ImportError:
    bw2test = pytest.mark.skip


def _package_data():
    a = np.arange(12, dtype=np.int64).reshape((3, 4))
    b = [(1, 1), (1, 2), (2, 3)]
    metadata = {
        'row from label': 'f1',
        'row to label': 'f3',
        'row dict': 'some_dict',
        'col from label': 'f2',
        'col to label': 'f4',
        'col dict': 'another_dict',
        'matrix': 'some_matrix'
    }
    frmt = lambda x: (x[0], x[1], 0, 0)
    dtype = [
        ('f1', np.uint32),
        ('f2', np.uint32),
        ('f3', np.uint32),
        ('f4', np.uint32),
    ]
    return a, b, 'foo', dtype, frmt, metadata

@pytest.fixture(scope="function")
@bw2test
def tempdir_package():
    with tempfile.TemporaryDirectory() as d:
        _, dirpath = create_presamples_package(
            [_package_data()],
            name='foo', id_='custom', dirpath=d
        )
        yield Path(dirpath)

@pytest.fixture
@bw2test
def package():
    _, dirpath = create_presamples_package(
        [_package_data()],
        name='foo', id_='custom'
    )
    return Path(dirpath)

@bw2test
def test_setup():
    assert Campaign.select().count() == 0
    assert PresampleResource.select().count() == 0
    assert CampaignOrdering.select().count() == 0

@bw2test
def test_campaign_ordering():
    c1 = Campaign.create(name="a")
    c2 = Campaign.create(name="b")
    assert c1 < c2
    assert sorted([c2, c1]) == [c1, c2]

@bw2test
def test_campaign_representation():
    c = Campaign.create(
        name='foo',
        description='bar',
    )
    assert str(c) == 'Campaign foo with no parent and 0 packages'
    c2 = Campaign.create(name='baz', parent=c)
    assert str(c2) == 'Campaign baz with parent foo and 0 packages'

@bw2test
def test_campaign_modified_autopopulate_autoupdate():
    c = Campaign.create(name='foo')
    assert isinstance(c.modified, datetime.datetime)
    dt = copy.copy(c.modified)
    time.sleep(0.5)
    c.save()
    assert dt < c.modified

@bw2test
def test_campaign_lineage():
    c1 = Campaign.create(name='a')
    c2 = Campaign.create(name='b', parent=c1)
    c3 = Campaign.create(name='c', parent=c1)
    c4 = Campaign.create(name='d', parent=c2)
    c5 = Campaign.create(name='e', parent=c3)
    c6 = Campaign.create(name='f', parent=c4)

    assert len(list(c1.ancestors)) == 0
    assert len(list(c1.descendants)) == 5

    assert c2.parent == c1
    assert list(c1.children) == [c2, c3]
    assert c4.parent == c2
    assert list(c4.children) == [c6]
    assert c6.parent == c4
    assert list(c6.children) == []

    assert list(c1.ancestors) == []
    assert list(c6.ancestors) == [c4, c2, c1]

    assert list(c6.descendants) == []
    assert list(c1.descendants) == [c2, c3, c4, c5, c6]

@bw2test
def test_campaign_packages_correct_in_order():
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr3)
    assert list(c.packages) == [pr1, pr3]
    c.add_presample_resource(pr2)
    assert list(c.packages) == [pr1, pr3, pr2]

@bw2test
def test_campaign_iteration():
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr3)
    c.add_presample_resource(pr2)
    for x, y in zip(c, 'acb'):
        assert x == y

@bw2test
def test_campaign_contains():
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    assert pr1 in c
    assert 'one' in c
    assert pr2 not in c
    assert 'two' not in c

@bw2test
def test_campaign_shift_presamples_at_index():
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr3)
    c.add_presample_resource(pr2)
    assert CampaignOrdering.get(package=pr1).order == 0
    assert CampaignOrdering.get(package=pr3).order == 1
    assert CampaignOrdering.get(package=pr2).order == 2

    c._shift_presamples_at_index(1)
    assert CampaignOrdering.get(package=pr1).order == 0
    assert CampaignOrdering.get(package=pr3).order == 2
    assert CampaignOrdering.get(package=pr2).order == 3

@bw2test
def test_campaign_max_order():
    # Make sure there are some gaps in the order
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    assert c._max_order() is None
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr3)
    c.add_presample_resource(pr2)
    assert c._max_order() == 2
    co = CampaignOrdering.get()
    co.order = 100
    co.save()
    assert c._max_order() == 100

@bw2test
def test_campaign_get_resource():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    assert c._get_resource(pr1) == pr1
    assert c._get_resource('one') == pr1

@bw2test
def test_campaign_get_resource_missing():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    assert c._get_resource(pr1) == pr1
    with pytest.raises(DoesNotExist):
        c._get_resource('two')

@bw2test
def test_campaign_replace_presample_package():
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr2)

    c.replace_presample_package(pr3, pr2)
    assert pr2 not in c
    assert pr3 in c
    assert CampaignOrdering.get(package=pr3).order == 1

@bw2test
def test_campaign_replace_presample_package_not_in_campaign():
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)

    with pytest.raises(MissingPresample):
        c.replace_presample_package(pr3, pr2)

@bw2test
def test_campaign_replace_presample_package_propagate():
    # Be sure one child doesn't have the original package
    pr1 = PresampleResource.create(name='one', path='a')
    pr2 = PresampleResource.create(name='two', path='b')
    pr3 = PresampleResource.create(name='three', path='c')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    c.add_presample_resource(pr2)

    c2 = c.add_child('test-2')
    c3 = c2.add_child('test-3')
    c4 = c3.add_child('test-4')

    c3.drop_presample_resource(pr2)

    c.replace_presample_package(pr3, pr2, propagate=True)
    assert pr2 not in c
    assert pr3 in c
    assert CampaignOrdering.get(campaign=c2, package=pr3).order == 1
    assert pr2 not in c2
    assert pr3 in c2
    assert CampaignOrdering.get(campaign=c2, package=pr3).order == 1
    assert pr2 not in c4
    assert pr3 in c4
    assert CampaignOrdering.get(campaign=c4, package=pr3).order == 1
    assert pr2 not in c3
    assert pr3 not in c3

@bw2test
def test_campaign_length():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    assert len(c) == 0
    c.add_presample_resource(pr1)
    assert len(c) == 1

@bw2test
def test_campaign_add_presample_resource():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    assert pr1 in c
    assert CampaignOrdering.get().order == 0

@bw2test
def test_campaign_add_presample_resource_index():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1, index=100)
    assert pr1 in c
    assert CampaignOrdering.get().order == 100
    assert len(c) == 1

@bw2test
def test_campaign_add_presample_resource_already_exists():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1)
    with pytest.raises(ValueError):
        c.add_presample_resource(pr1)

@bw2test
def test_drop_presample_resource():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    c.add_presample_resource(pr1, index=100)
    assert len(c) == 1
    c.drop_presample_resource(pr1)
    assert not len(c)
    assert not CampaignOrdering.select().count()

@bw2test
def test_drop_presample_resource_missing():
    pr1 = PresampleResource.create(name='one', path='a')
    c = Campaign.create(name='test-campaign')
    with pytest.raises(ValueError):
        c.drop_presample_resource(pr1)

def test_campaign_add_local_presamples_no_copy(tempdir_package):
    c = Campaign.create(name='test-campaign')
    c.add_local_presamples(tempdir_package, copy=False)
    assert len(c) == 1
    pr1 = PresampleResource.get()
    assert Path(pr1.path) == tempdir_package
    pp = PresamplesPackage(tempdir_package)
    assert pr1.name == pp.metadata['name']
    assert pp.metadata == pr1.metadata
    co = CampaignOrdering.get()
    assert co.campaign == c
    assert co.package == pr1
    assert co.order == 0

def test_campaign_add_local_presamples_no_copy_index(tempdir_package):
    c = Campaign.create(name='test-campaign')
    c.add_local_presamples(tempdir_package, index=10, copy=False)
    assert len(c) == 1
    co = CampaignOrdering.get()
    assert co.order == 10

def test_campaign_add_local_presamples_copy(tempdir_package):
    c = Campaign.create(name='test-campaign')
    from bw2data import projects
    print("Projects.dir:", projects.dir)
    c.add_local_presamples(tempdir_package)
    assert len(c) == 1
    pr1 = PresampleResource.get()
    assert Path(pr1.path) != tempdir_package
    assert os.listdir(pr1.path) == os.listdir(tempdir_package)
    PresamplesPackage(pr1.path)
    PresamplesPackage(tempdir_package)

def test_campaign_add_local_presamples_copy_already_exists(tempdir_package):
    c = Campaign.create(name='test-campaign')
    from bw2data import projects
    print("Projects.dir:", projects.dir)
    c.add_local_presamples(tempdir_package)
    with pytest.raises(ValueError):
        c.add_local_presamples(tempdir_package)

@bw2test
def test_campaign_add_child():
    c = Campaign.create(name='one')
    c2 = c.add_child('two', 'foo')
    assert c2.name == 'two'
    assert c2.description == 'foo'
    assert c2.parent == c
    assert c.parent is None

@bw2test
def test_campaign_add_child_already_exists():
    c = Campaign.create(name='one')
    c2 = c.add_child('two')
    with pytest.raises(ValueError):
        c2 = c.add_child('two')
