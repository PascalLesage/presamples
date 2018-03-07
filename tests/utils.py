import pytest
from presamples.utils import *


def test_name_conflicts():
    assert check_name_conflicts(['ABC', 'DEF']) is None
    with pytest.raises(NameConflicts):
        check_name_conflicts(['ABC', 'CDEF'])
