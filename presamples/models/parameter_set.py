from ..packaging import create_presamples_package
from bw2parameters import ParameterSet
from numpy import stack

def create_presamples_package_from_paramater_set(parameter_set, label, iterations=1000,
                                                 name=None, id_=None, overwrite=False,
                                                 dirpath=None, seed=None):
    """ Helper function to create a presamples package directly from a ParameterSet object"""
    assert isinstance(parameter_set, ParameterSet)
    data = parameter_set.evaluate_monte_carlo(iterations)
    names = sorted(list(data.keys()))
    array = stack([data[name] for name in names], axis=0)
    id_, dirpath = create_presamples_package(parameter_data=[(array, names, label)],
                                             name=name, id_=id_, overwrite=overwrite,
                                             dirpath=dirpath, seed=seed
                                             )
    return id_, dirpath