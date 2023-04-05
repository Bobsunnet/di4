class GeneralException(Exception):
    """Общее исключение программы"""


class InvalidDataField(GeneralException):
    """Исключение при неправильном заполнении поля"""


if __name__ == '__main__':
    err = InvalidDataField()
    raise InvalidDataField


