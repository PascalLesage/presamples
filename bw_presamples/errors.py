class BWParameterError(Exception):
    pass

class MissingPresample(BWParameterError):
    """The given presample is not present or available"""
    pass

class IncompatibleIndices(BWParameterError):
    """Indices have incompatible data types"""
    pass

class ConflictingLabels(BWParameterError):
    """Conflicting labels in the presample metadata"""
    pass
