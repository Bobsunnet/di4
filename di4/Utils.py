class DataOperator:
    """Хранит в себе данные о текущем состоянии программы, активных ячейках и т.д."""
    def __init__(self):
        self.cell_info = {}
        self.model_list:list = []
        self.selected_rows_ids = None
        self.active_model_info ={'sorted_asc':False, 'sorted_column':None, 'active_model':None}

    def get_cell_info(self, key:str):
        """ :param key: info type(index or model) """
        return self.cell_info.get(key)

    def set_cell_info(self, index, model):
        self.cell_info['index'] = index
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
