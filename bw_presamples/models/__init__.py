from .fixed_sum import FixedSum
from .kronecker_delta import KroneckerDelta


has_matrix_presamples = lambda lst: [o for o in lst if o.matrix_presamples()]
has_parameter_presamples = lambda lst: [o for o in lst if o.parameter_presamples()]
