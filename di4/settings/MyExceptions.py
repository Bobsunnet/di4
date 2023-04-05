
#todo сделать нормальные исключения
class GeneralException(Exception):
    pass


class ModelNotFound(GeneralException):
    pass


class InvalidDataField(GeneralException):
    pass


if __name__ == '__main__':
    err = InvalidDataField()
    raise InvalidDataField


