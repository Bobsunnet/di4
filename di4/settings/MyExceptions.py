class GeneralException(Exception):
    """Общее исключение программы"""

    def __str__(self):
        return 'App General Exception'


class InvalidDataField(GeneralException):
    """Исключение при неправильном заполнении поля"""

    def __str__(self):
        return 'Field Input Exception'


if __name__ == '__main__':
    err = InvalidDataField()
    raise InvalidDataField


