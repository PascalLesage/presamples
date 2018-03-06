from ..packaging import create_presamples_package
from ..campaigns import PresampleResource
from pathlib import Path


class ModelBase:
    """Base class that provides convenience methods for creating presample packages.

    Can be passed directly to ``create_presamples_package``. Can also directly create a presample package or a ``PresampleResource``.

    If a subclass will create matrix presamples, then the following must be create or defined:

        * ``selff.matrix_array``: Numpy array of pre-calculated samples
        * ``self.indices``: Indices in the correct data type for the matrices to be populated.

    If a subclass will create parameter presamples, then the following must be create or defined:

        * ``self.parameter_array``: Numpy array of pre-calculated samples
        * ``self.names``: List of parameter names

   """
    @property
    def matrix_data(self):
        return []

    @property
    def parameter_data(self):
        return []

    def create_presample_package(self, name=None, id_=None, dirpath=None):
        """Create a presamples package. Input arguments are the same as in ``create_presamples_package``."""
        kwargs = {
            'name': name,
            'id_': id_,
            'dirpath': dirpath,
            'matrix_data': [self],
            'parameter_data': [self],
        }
        return create_presamples_package(**kwargs)

    def create_stored_presample_package(self, name, description=None, id_=None, dirpath=None):
        _, dirpath = self.create_presample_package(name=name, id_=id_, dirpath=dirpath)
        return PresampleResource.create(
            name=name,
            description=description,
            path=dirpath
        )
