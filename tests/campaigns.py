from bw2data.tests import bw2test
from bw_presamples.campaigns import *
import copy
import datetime
import time


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
    assert str(c) == 'Campaign foo with no parent and 0 resources'
    assert repr(c) == str(c)
    c2 = Campaign.create(name='baz', parent=c)
    assert str(c2) == 'Campaign baz with parent foo and 0 resources'

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
