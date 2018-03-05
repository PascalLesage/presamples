# from presamples import (
#     ParameterPresamples,
#     create_presamples_package,
#     append_presamples_package,
# )
# from presamples.parameter_presamples import NameConflicts
# from pathlib import Path
# import numpy as np
# import pytest
# import tempfile

# try:
#     from bw2data import mapping
#     from bw2data.tests import bw2test
# except ImportError:
#     bw2test = pytest.mark.skip


# @pytest.fixture
# def basic():
#     with tempfile.TemporaryDirectory() as d:
#         dirpath = Path(d)
#         s1 = np.arange(16, dtype=np.int64).reshape((4, 4))
#         s2 = np.arange(12, dtype=np.int64).reshape((3, 4))
#         n1 = list('ABCD')
#         n2 = list('DEF')
#         id_, dirpath = create_presamples_package(
#             parameter_presamples=[(s1, n1, 'winter'), (s2, n2, 'summer')], name='foo', id_='bar', dirpath=dirpath
#         )
#         yield dirpath

# def test_basic_presamples_class(basic):
#     pp = ParameterPresamples(basic)
#     assert len(pp) == 2
#     assert list(pp) == ['winter', 'summer']
#     assert list(pp['winter']) == list('ABCD')
#     assert 'winter' in pp
#     assert 'summer' in pp
#     assert len(pp.data) == 2
#     assert np.allclose(pp['winter']['A'], np.arange(4))
#     with pytest.raises(NameConflicts):
#         pp.flattened()

# def test_basic_presamples_filtered(basic):
#     pp = ParameterPresamples(basic, labels='winter')
#     assert len(pp) == 1
#     assert list(pp) == ['winter']
#     assert list(pp['winter']) == list('ABCD')
#     assert 'winter' in pp
#     assert 'summer' not in pp
#     assert np.allclose(pp['winter']['A'], np.arange(4))
#     assert list(pp.flattened()) == list("ABCD")

# @bw2test
# def test_skip_matrix_presamples():
#     mapping.add('ABCDEF')
#     t1 = [('A', 'A', 0), ('A', 'B', 1), ('B', 'C', 3)]
#     t2 = np.arange(12, dtype=np.int64).reshape((3, 4))
#     b1 = [('A', 'D'), ('A', 'E'), ('B', 'F')]
#     b2 = np.arange(12, dtype=np.int64).reshape((3, 4))
#     c1 = 'DEF'
#     c2 = np.arange(12, dtype=np.int64).reshape((3, 4))
#     inputs = [
#         (t2, t1, 'technosphere'),
#         (b2, b1, 'biosphere'),
#         (c2, c1, 'cf'),
#     ]
#     s1 = np.arange(16, dtype=np.int64).reshape((4, 4))
#     s2 = np.arange(12, dtype=np.int64).reshape((3, 4))
#     n1 = list('ABCD')
#     n2 = list('DEF')
#     id_, dirpath = create_presamples_package(
#         inputs, [(s1, n1, 'winter'), (s2, n2, 'summer')], name='foo', id_='bar'
#     )
#     pp = ParameterPresamples(dirpath)
#     assert len(pp) == 2
