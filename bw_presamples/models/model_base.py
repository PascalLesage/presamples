from ..packaging import create_presamples_package
from ..campaigns import PresampleResource
from pathlib import Path


class ModelBase:
    """Base class that provides convenience methods for creating presample packages.

    Can be passed directly to ``create_presamples_package``. Can also directly create a presample package or a ``PresampleResource``.

   If a subclass will create matrix presamples, then the following must be create or defined:

        * ``self.array``: Numpy array of pre-calculated samples
        * ``matrix_label``: Label of matrix where samples will be inserted, e.g. "technosphere"
        * ``self.indices``: Indices in the correct data type for the matrices to be populated.

    If a subclass will create parameter presamples, then the following must be create or defined:

        * ``self.array``: Numpy array of pre-calculated samples
        * ``self.names``: List of parameter names

   """
    def matrix_presamples(self):
        try:
            return (self.array, self.indices, self.matrix_label)
        except AttributeError:
            return None

    def parameter_presamples(self):
        try:
            return (self.array, self.names)
        except AttributeError:
            return None

    def create_presample_package(self, name=None, id_=None, dirpath=None):
        """Create a presamples package. Input arguments are the same as in ``create_presamples_package``. Automatically populates both matrix and parameter presamples as needed."""
        kwargs = {
            'name': name,
            'id_': id_,
            'dirpath': dirpath
        }
        if self.matrix_presamples():
            kwargs['matrix_presamples'] = self.matrix_presamples()
        if self.parameter_presamples():
            kwargs['parameter_presamples'] = self.parameter_presamples()
        return create_presamples_package(**kwargs)

    def create_presample_resource(self, name, description=None, id_=None, dirpath=None):
        _, dirpath = self.create_presamples_package(name=name, id_=id_, dirpath=dirpath)
        return PresampleResource.create(
            name=name,
            description=description,
            resource=dirpath
        )
