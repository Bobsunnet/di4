
#todo сделать нормальные исключения
class GeneralException(Exception):
    pass


class ModelNotFound(GeneralException):
    pass


