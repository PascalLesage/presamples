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
