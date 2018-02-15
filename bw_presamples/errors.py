class BWParameterError(Exception):
    pass

class MissingPresample(BWParameterError):
    """The given presample is not present or available"""
    pass
