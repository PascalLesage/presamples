from presamples import *
import numpy as np
import pytest

try:
    from bw2data import mapping, Database, get_activity
    from bw2data.tests import bw2test
    from bw2data.parameters import (
        ActivityParameter,
        DatabaseParameter,
        Group,
        ProjectParameter,
        parameters,
    )
    from presamples.models import ParameterizedBrightwayModel
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
    pbm = ParameterizedBrightwayModel("A")
    pbm.load_parameter_data()
    expected = {
        'A__a1': {
            'amount': 7.0,
           'code': 'A1',
           'database': 'db',
           'formula': '(((B__b1 + C__c1) - db__db1) - 2)',
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
    assert pbm.data == expected

@bw2test
def test_load_existing_complete():
    # Use same structure as in complicated example, but pre-create some presamples packages
    # Start with `project`
    ProjectParameter.create(
        name="p1",
        amount=1,
    )
    ProjectParameter.create(
        name="p2",
        amount=1,
    )
    parameters.recalculate()
    pbm = ParameterizedBrightwayModel("project")
    pbm.load_parameter_data()
    result = pbm.calculate_static()
    expected = {'project__p1': 1, 'project__p2': 1}
    assert result == expected
    for obj in pbm.data.values():
        obj['amount'] = 10
    _, dirpath_project = pbm.save_presample('project-test')
    pp = PresamplesPackage(dirpath_project)
    assert len(pp) == 1
    assert pp.parameters['project__p1'] == 10

    # We will also do group 'D'; this will include database parameters, which will we purge ourselves
    Database("db").register()
    Group.create(name="D", order=[])
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
    parameters.recalculate()
    pbm = ParameterizedBrightwayModel("D")
    pbm.load_existing(dirpath_project)
    expected = {'project__p1': 10, 'project__p2': 10}
    assert pbm.global_params == expected

    pbm.load_parameter_data()
    expected = {
        'D__d1': {
            'database': 'db',
            'code': 'D1',
            'formula': '(project__p1 + db__db1)',
            'amount': 3.0,
            'original': 'd1'},
        'db__db1': {
            'database': 'db',
            'formula': '(2 * project__p1)',
            'amount': 2.0,
            'original': 'db1'},
        'db__db2': {
            'database': 'db',
            'amount': 2.0,
            'original': 'db2'},
    }
    assert pbm.data == expected

    # Want to calculate database parameters dynamically
    pbm.data = {'D__d1': pbm.data['D__d1']}
    pbm.data['D__d1']['amount'] = 12
    _, dirpath_d = pbm.save_presample('D-test')
    pp = PresamplesPackage(dirpath_d)
    assert len(pp) == 1
    assert pp.parameters['D__d1'] == 12

    # Create rest of parameters
    Group.create(name="E", order=[])
    Group.create(name="B", order=["E"])
    Group.create(name="C", order=["D", "E"])
    Group.create(name="A", order=["C", "B"])
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
    pbm = ParameterizedBrightwayModel("A")
    pbm.load_existing(dirpath_project)
    pbm.load_existing(dirpath_d)
    pbm.load_parameter_data()
    expected = {
        'A__a1': {
            'amount': 7.0,
           'code': 'A1',
           'database': 'db',
           'formula': '(((B__b1 + C__c1) - db__db1) - 2)',
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
    }
    assert pbm.data == expected
    result = pbm.calculate_static()

    expected = {
        'A__a1': 70.0,
        'B__b1': 42.0,
        'C__c1': 50.0,
        'E__e1': 22.0,
        'db__db1': 20.0,
        'db__db2': 2.0
    }
    assert result == expected

    pbm = ParameterizedBrightwayModel("A")
    pbm.load_existing(dirpath_project, only=['project__p1'])
    pbm.load_existing(dirpath_d)
    pbm.load_parameter_data()
    assert 'project__p2' in pbm.data
    assert 'project__p1' not in pbm.data


@bw2test
def test_append_package():
    ProjectParameter.create(
        name="p1",
        amount=1,
    )
    ProjectParameter.create(
        name="p2",
        amount=1,
    )
    parameters.recalculate()
    pbm = ParameterizedBrightwayModel("project")
    pbm.load_parameter_data()
    pbm.calculate_static()
    for obj in pbm.data.values():
        obj['amount'] = 10
    _, dirpath = pbm.save_presample('project-test')
    pp = PresamplesPackage(dirpath)
    assert len(pp) == 1
    assert pp.parameters['project__p1'] == 10

    Database("db").register()
    Group.create(name="D", order=[])
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
    parameters.recalculate()
    pbm = ParameterizedBrightwayModel("D")
    pbm.load_existing(dirpath)
    expected = {'project__p1': 10, 'project__p2': 10}
    assert pbm.global_params == expected

    pbm.load_parameter_data()
    pbm.data = {'D__d1': pbm.data['D__d1']}
    pbm.data['D__d1']['amount'] = 12
    _, dp = pbm.append_presample(dirpath, 'D-test')
    assert dp == dirpath
    pp = PresamplesPackage(dirpath)
    assert len(pp) == 2
    assert pp.parameters['D__d1'] == 12
    assert pp.parameters['project__p1'] == 10

@bw2test
def test_calculate_stochastic():
    Database("db").register()
    ProjectParameter.create(
        name="p1",
        amount=1,
    )
    ProjectParameter.create(
        name="p2",
        amount=1,
    )
    parameters.recalculate()
    pbm = ParameterizedBrightwayModel("project")
    pbm.load_parameter_data()
    pbm.data['project__p1']['amount'] = np.ones(10) + 100
    pbm.data['project__p2']['amount'] = np.ones(10) + 10
    _, dirpath_project = pbm.save_presample('project-test')

    pp = PresamplesPackage(dirpath_project)
    assert len(pp) == 1
    assert np.allclose(pp.parameters['project__p1'], np.ones(10) + 100)

    # Create rest of parameters
    Group.create(name="E", order=[])
    ActivityParameter.create(
        group="E",
        database="db",
        code="E1",
        name="e1",
        formula="p1 + p2 + e2",
        amount=4,
    )
    ActivityParameter.create(
        group="E",
        database="db",
        code="E2",
        name="e2",
        amount=1,
        data={'uncertainty type': 4, 'minimum': 1000, 'maximum': 1100}
    )
    parameters.recalculate()
    pbm = ParameterizedBrightwayModel("E")
    pbm.load_existing(dirpath_project)
    pbm.load_parameter_data()
    result = pbm.calculate_stochastic(10)

    assert np.allclose(result['project__p1'], [101] * 10)
    assert np.allclose(result['project__p2'], [11] * 10)
    assert all(result['E__e2'] >= 1000)
    assert all(result['E__e2'] <= 1100)
    assert np.allclose(result['E__e1'], result['E__e2'] + 101 + 11)

@bw2test
def test_calculate_matrix_presamples():
    data = {
        ("test-db", 'b'): {
            'exchanges': [],
            'type': 'emission',
            },
        ("test-db", 't1'): {
            'exchanges': [{
                'amount': 1,
                'input': ('test-db', 't2'),
                'type': 'technosphere',
                'formula': 'foo + bar'},
                {'amount': 1,
                'input': ('test-db', 'b'),
                'type': 'biosphere',
                'formula': 'foo - bar + pppp'}],
            'type': 'process',
            },
        ("test-db", 't2'): {
            'exchanges': [],
            'type': 'process',
            },
    }
    Database("test-db").write(data)
    Group.create(name="E", order=[])
    data = [{
        'name': 'foo',
        'database': 'test-db',
        'code': 't1',
        'amount': 7,
        'uncertainty_type': 4,
        'minimum': 0,
        'maximum': 14,
    }, {
        'name': 'bar',
        'database': 'test-db',
        'code': 't1',
        'amount': 11,
    }]
    parameters.new_project_parameters([{'name': 'pppp', 'amount': 12}])
    parameters.new_activity_parameters(data, 'A')
    parameters.add_exchanges_to_group('A', get_activity(("test-db", 't1')))
    parameters.recalculate()

    pbm = ParameterizedBrightwayModel("A")
    pbm.load_parameter_data()
    pbm.calculate_static()
    pbm.calculate_matrix_presamples()
    id_, dirpath = pbm.save_presample('test-everything')

    # Check for file contents
    pp = PresamplesPackage(dirpath)
    resources = pp.resources
    assert len(resources) == 3
    assert resources[0]['type'] == 'biosphere'
    assert resources[0]['samples']['shape'] == [1, 1]
    assert resources[1]['type'] == 'technosphere'
    assert resources[1]['samples']['shape'] == [1, 1]
    assert resources[2]['label'] == 'test-everything'
    assert resources[2]['samples']['shape'] == [3, 1]

@bw2test
def test_calculate_matrix_presamples_single_row():
    pass
