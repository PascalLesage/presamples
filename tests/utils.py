from presamples.utils import *
import numpy as np
import os
import pytest


basedir = os.path.dirname(os.path.abspath(__file__))

def test_name_conflicts():
    assert check_name_conflicts(['ABC', 'DEF']) is None
    with pytest.raises(NameConflicts):
        check_name_conflicts(['ABC', 'CDEF'])

def test_convert_parameter_dict_to_presamples():
    data = {
        'b': np.arange(5),
        'a': np.arange(5, 10)
    }
    expected = (
        ['a', 'b'],
        np.array([[5, 6, 7, 8, 9], [0, 1, 2, 3, 4]])
    )
    result = convert_parameter_dict_to_presamples(data)
    assert expected[0] == result[0]
    assert np.allclose(expected[1], result[1])

def test_convert_parameter_dict_to_presamples_error():
    data = {
        'b': np.arange(5),
        'a': np.arange(5, 15)
    }
    with pytest.raises(ValueError):
        convert_parameter_dict_to_presamples(data)

def test_md5():
    expected = "700c072345111586ddb5b90ea8018fc8"
    assert md5(os.path.join(basedir, "random.nonsense")) == expected
