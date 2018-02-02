__all__ = [
    'Campaign',
    'convert_parameter_dict_to_presamples',
    'create_presamples_package',
    'FORMATTERS',
    'IrregularPresamplesArray',
    'MatrixPresamples',
    'PresamplePackage',
    'split_inventory_presamples',
]


__version__ = (0, 0, 'dev')

from .campaigns import Campaign, PresamplePackage
from .array import IrregularPresamplesArray
from .packaging import (
    create_presamples_package,
    FORMATTERS,
    split_inventory_presamples,
)
from .matrix_presamples import MatrixPresamples

from .utils import (
    convert_parameter_dict_to_presamples,
)
