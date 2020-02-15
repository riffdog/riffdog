
class RiffDogException(Exception):
    pass


class ResourceNotFoundError(RiffDogException):
    pass


class StorageNotImplemented(RiffDogException):
    pass
