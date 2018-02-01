from bw2data.backends.peewee.proxies import Exchange
from bw2data.backends.peewee.schema import ExchangeDataset
from .model_base import ModelBase


class SelectedExchangesBase(ModelBase):
    """Base class for presample models which take a selection of exchanges."""
    matrix_label = "technosphere" # Default, can be changed

    def find_exchanges(self, data):
        """Find exchanges and return in a common format. ``data`` is a list of objects used to find exchanges.

        Exchanges can be specified by:

        * A dictionary in the correct format already.
        * ``(input key, output key)``. Will raise a ``ValueError`` if multiple exchanges match.
        * ``(input key, output key, type)``. Type is an exchange type as a string, e.g. technosphere. Will raise a ``ValueError`` if multiple exchanges match.
        * ``bw2data.backends.peewee.proxies.Exchange`` object.

        ``data`` can have mixed types.

        Exchanges are returned as dictionaries, with at least the following keys:

        * input: input key, e.g. ('foo', 'bar')
        * output: output key, e.g. ('foo', 'bar')
        * amount: float
        * type: str, e.g. production

        Most exchanges also include keys like "uncertainty type", "unit", and "name", but do not rely on these keys being present.

        """
        return [self._finder(obj) for obj in data]

    def _finder(self, obj):
        if isinstance(obj, dict):
            return obj
        elif isinstance(obj, Exchange):
            return obj._data
        elif isinstance(obj, (list, tuple)) and len(obj) == 2:
            (input_db, input_code), (output_db, output_code) = obj
            qs = ExchangeDataset.select().where(
                input_code=input_code,
                input_database=input_db,
                output_code=output_code,
                output_database=output_db
            )
            if qs.count() != 1:
                raise ValueError("Can't find one exchange for inputs: {}".format(obj))
            return Exchange(qs.get())._data
        elif isinstance(obj, (list, tuple)) and len(obj) == 3:
            (input_db, input_code), (output_db, output_code), kind = obj
            qs = ExchangeDataset.select().where(
                input_code=input_code,
                input_database=input_db,
                output_code=output_code,
                output_database=output_db,
                type=kind
            )
            if qs.count() != 1:
                raise ValueError("Can't find one exchange for inputs: {}".format(obj))
            return Exchange(qs.get())._data
        else:
            raise ValueError("Can't understand this exchange identifier: {}".format(obj))

    @property
    def indices(self):
        if self.matrix_label == "technosphere":
            return [(o['input'], o['output'], o['type']) for o in self.data]
        elif self.matrix_label == "cf":
            raise NotImplementedError("This model is not defined for LCIA CFs")
        else:
            return [(o['input'], o['output']) for o in self.data]
