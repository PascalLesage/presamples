__all__ = [
    'create_matrix_presamples_package',
    'IrregularPresamplesArray',
    'MatrixPresamples',
]


__version__ = (0, 0, 'dev')

from .array import IrregularPresamplesArray
from .packaging import create_matrix_presamples_package
from .matrix_presamples import MatrixPresamples
