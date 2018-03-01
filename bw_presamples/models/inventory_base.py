from ..packaging import split_inventory_presamples
from .model_base import ModelBase
try:
    from bw2data.backends.peewee.proxies import Exchange
    from bw2data.backends.peewee.schema import ExchangeDataset
except ImportError:
    Exchange = ExchangeDataset = None


class InventoryBaseModel(ModelBase):
    """Base class for presample models which take a selection of inventory exchanges."""
    def find_exchanges(self, data):
        """Find exchanges and return in a common format. ``data`` is a list of objects used to find exchanges.

        Exchanges can be specified by:

        * A dictionary in the correct format already.
        * ``(input key, output key)``. Will raise a ``ValueError`` if multiple exchanges match.
        * ``(input key, output key, type)``. Type is an exchange type as a string, e.g. technosphere. Will raise a ``ValueError`` if multiple exchanges match.
        * ``bw2data.backends.peewee.proxies.Exchange`` object.

        If Brightway2 is not installed, only dictionaries can be used.

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
        elif not Exchange:
            raise ImportError("Brightway2 not installed")
        elif isinstance(obj, Exchange):
            return obj._data
        elif isinstance(obj, (list, tuple)) and len(obj) == 2:
            (input_db, input_code), (output_db, output_code) = obj
            qs = ExchangeDataset.select().where(
                ExchangeDataset.input_code==input_code,
                ExchangeDataset.input_database==input_db,
                ExchangeDataset.output_code==output_code,
                ExchangeDataset.output_database==output_db
            )
            if qs.count() != 1:
                raise ValueError("Can't find one exchange for inputs: {}".format(obj))
            return Exchange(qs.get())._data
        elif isinstance(obj, (list, tuple)) and len(obj) == 3:
            (input_db, input_code), (output_db, output_code), kind = obj
            qs = ExchangeDataset.select().where(
                ExchangeDataset.input_code==input_code,
                ExchangeDataset.input_database==input_db,
                ExchangeDataset.output_code==output_code,
                ExchangeDataset.output_database==output_db,
                ExchangeDataset.type==kind
            )
            if qs.count() != 1:
                raise ValueError("Can't find one exchange for inputs: {}".format(obj))
            return Exchange(qs.get())._data
        else:
            raise ValueError("Can't understand this exchange identifier: {}".format(obj))

    @property
    def matrix_data(self):
        if not hasattr(self, "matrix_array"):
            raise ValueError("Must run model first")

        reformat = lambda lst: [(o['input'], o['output'], o['type']) for o in lst]
        return split_inventory_presamples(self.matrix_array, reformat(self.data))
