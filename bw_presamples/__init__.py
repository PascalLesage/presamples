__all__ = [
    'append_presamples_package',
    'Campaign',
    'convert_parameter_dict_to_presamples',
    'create_presamples_package',
    'FORMATTERS',
    'Indexer',
    'IrregularPresamplesArray',
    'PackagesDataLoader',
    'PresampleResource',
    'PresamplesPackage',
    'split_inventory_presamples',
]


__version__ = (0, 0, 'dev0')

from .campaigns import Campaign, PresampleResource
from .indexer import Indexer
from .array import IrregularPresamplesArray
from .packaging import (
    append_presamples_package,
    create_presamples_package,
    FORMATTERS,
    split_inventory_presamples,
)
from .package_interface import PresamplesPackage
from .loader import PackagesDataLoader
from .utils import (
    convert_parameter_dict_to_presamples,
)
