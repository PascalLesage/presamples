import pytest

try:
    from bw2data import mapping, Database
    from bw2data.tests import bw2test
    from bw2data.parameters import (
        ActivityParameter,
        DatabaseParameter,
        Group,
        ProjectParameter,
        parameters,
    )
    from bw_presamples.models import ParameterizedBrightwayModel
except ImportError:
    bw2test = pytest.mark.skip


@bw2test
def test_chain_loading():
    Database("B").register()
    Database("K").register()
    Group.create(name="G", order=["A"])
    ActivityParameter.create(
        group="A",
        database="B",
        code="C",
        name="D",
        formula="2 ** 3",
        amount=1,

    )
    ActivityParameter.create(
        group="A",
        database="B",
        code="E",
        name="F",
        formula="foo + bar + D",
        amount=2,
    )
    ActivityParameter.create(
        group="G",
        database="K",
        code="H",
        name="J",
        formula="F + D * 2",
        amount=3,
    )
    DatabaseParameter.create(
        database="B",
        name="foo",
        formula="2 ** 2",
        amount=5,
    )
    ProjectParameter.create(
        name="bar",
        formula="2 * 2 * 2",
        amount=6,
    )
    parameters.recalculate()
    m = ParameterizedBrightwayModel("A")
    m.load_parameter_data()
    expected = {
        'A__D': {
            'database': 'B',
            'code': 'C',
            'formula': '(2 ** 3)',
            'amount': 8.0,
            'original': 'D'
        },
        'A__F': {
            'database': 'B',
            'code': 'E',
            'formula': '((B__foo + project__bar) + A__D)',
            'amount': 20.0,
            'original': 'F'
        },
        'B__foo': {
            'database': 'B',
            'formula': '(2 ** 2)',
            'amount': 4.0,
            'original': 'foo'
        },
        'project__bar': {
            'formula': '((2 * 2) * 2)',
            'amount': 8.0,
            'original': 'bar'
        }
    }
    assert m.data == expected

@bw2test
def test_chain_loading_complicated():
    Database("db").register()
    Group.create(name="D", order=[])
    Group.create(name="E", order=[])
    Group.create(name="B", order=["E"])
    Group.create(name="C", order=["D", "E"])
    Group.create(name="A", order=["C", "B"])
    ProjectParameter.create(
        name="p1",
        amount=1,
    )
    ProjectParameter.create(
        name="p2",
        amount=1,
    )
    DatabaseParameter.create(
        database="db",
        name="db1",
        formula="2 * p1",
        amount=2,
    )
    DatabaseParameter.create(
        database="db",
        name="db2",
        amount=2,
    )
    ActivityParameter.create(
        group="D",
        database="db",
        code="D1",
        name="d1",
        formula="p1 + db1",
        amount=3,
    )
    ActivityParameter.create(
        group="E",
        database="db",
        code="E1",
        name="e1",
        formula="p1 + p2 + db2",
        amount=4,
    )
    ActivityParameter.create(
        group="C",
        database="db",
        code="C1",
        name="c1",
        formula="(e1 - d1) * 5",
        amount=5,
    )
    ActivityParameter.create(
        group="B",
        database="db",
        code="B1",
        name="b1",
        formula="e1 * 2 - 2",
        amount=6,
    )
    ActivityParameter.create(
        group="A",
        database="db",
        code="A1",
        name="a1",
        formula="b1 + c1 - db1 - 2",
        amount=7,
    )
    parameters.recalculate()
    m = ParameterizedBrightwayModel("A")
    m.load_parameter_data()
    expected = {
        'A__a1': {
            'amount': 7.0,
           'code': 'A1',
           'database': 'db',
           'formula': '(((B__b1 + C__c1) - db__db1) - 1)',
           'original': 'a1'},
        'B__b1': {
            'amount': 6.0,
           'code': 'B1',
           'database': 'db',
           'formula': '((E__e1 * 2) - 2)',
           'original': 'b1'},
        'C__c1': {
            'amount': 5.0,
           'code': 'C1',
           'database': 'db',
           'formula': '((E__e1 - D__d1) * 5)',
           'original': 'c1'},
        'D__d1': {
            'amount': 3.0,
           'code': 'D1',
           'database': 'db',
           'formula': '(project__p1 + db__db1)',
           'original': 'd1'},
        'E__e1': {
            'amount': 4.0,
            'code': 'E1',
            'database': 'db',
            'formula': '((project__p1 + project__p2) + db__db2)',
            'original': 'e1'},
        'db__db1': {
            'amount': 2.0,
            'database': 'db',
            'formula': '(2 * project__p1)',
            'original': 'db1'},
        'db__db2': {
            'amount': 2.0,
            'database': 'db',
            'original': 'db2'},
        'project__p1': {
            'amount': 1.0,
            'original': 'p1'},
        'project__p2': {
            'amount': 1.0,
            'original': 'p2'}
    }
    assert m.data == expected
