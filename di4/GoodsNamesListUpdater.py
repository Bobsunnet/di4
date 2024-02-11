from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import Qt

from di4 import dbConnector



class GoodsNamesList:
    goods_names_list_instance = None
    __isCreated = False

    def __new__(cls, *args, **kwargs):
        if not cls.goods_names_list_instance:
            cls.goods_names_list_instance = object.__new__(cls, *args, **kwargs)
        return cls.goods_names_list_instance

    def __init__(self):
        if not self.__isCreated:
            self.goods_names_list = []
            self.update_goods_names_list()
            self._created()

    @classmethod
    def _created(cls):
        if not cls.__isCreated:
            cls.__isCreated = True

    def update_goods_names_list(self) ->list:
        self.goods_names_list = [g[0] for g in dbConnector.select_goods_name()]
        return self.goods_names_list

    def get_goods_names_list(self) ->list:
        return self.goods_names_list

    def create_completer(self):
        completer = QCompleter(self.goods_names_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        return completer


def main_test():
    g_list1 = GoodsNamesList() # здесь идет обращение к базе при создании нового обьекта
    g_list2 = GoodsNamesList() # а здесь уже обращение к базе при инициализации не происходит

    print(g_list1.get_goods_names_list())
    print(g_list2.get_goods_names_list())




if __name__ == '__main__': 
    main_test()
