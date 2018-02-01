import numpy as np


def convert_parameter_dict_to_presamples(parameters):
    """Convert a dictionary of named parameters to the form needed for ``parameter_presamples``.

    ``parameters`` should be a dictionary with names (as strings) as keys and Numpy arrays as values. All Numpy arrays should have the same shape.

    Returns (numpy samples array, list of names).

    """
    names = sorted(parameters.keys())
    shapes = {obj.shape for obj in parameters.values()}
    if len(shapes) != 1:
        raise ValueError(
            "Hetergeneous array shapes ({}) not allowed".format(shapes)
        )
    return names, np.vstack([parameters[key].reshape((1, -1)) for key in names])
