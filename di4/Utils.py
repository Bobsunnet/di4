from PyQt5.QtCore import Qt


class ColumnOperator:
    """ Хранит временные данные по сортировке колонки и имени хедера, меняет значки сортировки """

    def __init__(self, stored_name: str):
        self._stored_model = None # Pyqt5 объект QSqlRelationTableModel
        self._stored_name: str = stored_name
        self.__asc_symbol = chr(0x2193) # ↓
        self.__desc_symbol = chr(0x2191) # ↑
        self.sorted_asc: bool = False
        self._stored_column: int | None = None

    @property
    def asc_symbol(self):
        return self.__asc_symbol

    @property
    def desc_symbol(self):
        return self.__desc_symbol

    def restore_col_header(self):
        """ Возвращает старое название Хедеру несортированного столбца """
        if self._stored_column:
            self._stored_model.setHeaderData(self._stored_column, Qt.Orientation.Horizontal, self._stored_name)

    def change_sorted_status(self, model, col):
        if self.sorted_asc:
            self.sorted_asc = False
        else:
            self.sorted_asc = True

        # если меняется модель или колонка, то статус сортировки сбрасывается
        if model != self._stored_model or col != self._stored_column:
            self.sorted_asc = False

    def change_header_name(self, model, col):
        self.restore_col_header()
        self._stored_name = model.headerData(col, Qt.Orientation.Horizontal)

        if self.sorted_asc:
            model.setHeaderData(col, Qt.Orientation.Horizontal, f'{self._stored_name} {self.desc_symbol}')
        else:
            model.setHeaderData(col, Qt.Orientation.Horizontal, f'{self._stored_name} {self.asc_symbol}')

        self._stored_column = col
        self._stored_model = model



class CurrentDataOperator:
    """Хранит в себе данные о текущем состоянии программы, активных ячейках и т.д."""

    def __init__(self):
        self.cell_info = {}
        self.models_list: list = []
        self.selected_rows_ids = None
        self.active_model_info = {'active_model': None}
        self.current_column = ColumnOperator('')

    def get_cell_info(self, key: str):
        """ :param key: info type(index or model) """
        return self.cell_info.get(key)

    def set_index(self, index):
        self.cell_info['index'] = index

    def set_model(self, model):
        self.cell_info['model'] = model

    def reset_cell_info(self):
        self.cell_info['index'] = None
        self.cell_info['model'] = None

    def set_active_model(self, model):
        self.active_model_info['active_model'] = model

    def get_active_model(self):
        return self.active_model_info['active_model']


def main():
    pass


if __name__ == '__main__':
    main()
