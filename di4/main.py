import re
import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

import dbConnector
from di4.settings import sql_pyqt
from di4.static import stylesheet

HEADERS_GOODS = ['Name', 'amount']
HEADERS_ORDERS = ['Name', 'sell_price', 'date']
HEADERS_PURCHASE = ['Name', 'buy_price', 'date']
HEADERS_STAT = ['Name', 'buy_price', 'sell_price', 'buy_date', 'sell_date']


class TextWidget(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()
        self.linked_cell = None

    def link_cell(self, cell: tuple):
        self.linked_cell = cell

    def get_linked_cell(self):
        return self.linked_cell


class TableWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(TableWindow, self).__init__()
        self.setup_ui()
        self.model_create(dbConnector.TABLE_GOODS, HEADERS_GOODS, 'model_goods')
        self.model_create(dbConnector.TABLE_PURCHASE, HEADERS_PURCHASE, 'model_purchase')
        self.model_create(dbConnector.TABLE_ORDERS, HEADERS_ORDERS, 'model_orders')

        self.create_table_view(getattr(self,'model_goods'), 'table_view_goods')
        self.create_table_view(getattr(self,'model_purchase'), 'table_view_purchase')
        self.create_table_view(getattr(self,'model_orders'), 'table_view_orders')
        # self.create_table_view(getattr(self,'model_goods'), 'table_view_goods')
        # self.model_create(dbConnector.TABLE_PURCHASE,HEADERS_PURCHASE,'model_stat')
        self.table_view_setup()
        self.widgets_setup()
        self.layout_setup()

    def model_create(self, table, headers, model_name):
        model = sql_pyqt.QSqlTableModel(db=sql_pyqt.db)
        model.setTable(table)
        model.setEditStrategy(sql_pyqt.QSqlTableModel.EditStrategy.OnFieldChange)
        model.sort(0, Qt.SortOrder.DescendingOrder)
        # for i, name in enumerate(headers):
        #     model.setHeaderData(i + 1, Qt.Orientation.Horizontal, name)

        model.select()
        print(model.columnCount())
        setattr(self, model_name, model)

    def create_table_view(self, model, obj_name):
        table_view = QtWidgets.QTableView()
        table_view.setObjectName(obj_name)
        table_view.setModel(model)
        # table_view.horizontalHeader().setStyleSheet(stylesheet.horizontal_header)
        # table_view.verticalHeader().setStyleSheet(stylesheet.vertical_header)
        table_view.hideColumn(0)
        for i in range(model.columnCount() - 1):
            table_view.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

        setattr(self, obj_name, table_view)

    def table_view_setup(self):
        self.table_view_stat = QtWidgets.QTableView()
        self.table_view_stat.setObjectName('table_view_stat')

        # при нажатии на ячейку срабатывает ивентлуп
        self.table_view_goods.selectionModel().currentChanged.connect(self.cell_highlighted)

    def widgets_setup(self):
        self.tab_widget = QtWidgets.QTabWidget()
        tab_widgets_list = [self.table_view_goods, self.table_view_purchase, self.table_view_orders,
                            self.table_view_stat]
        for widg in tab_widgets_list:
            self.tab_widget.addTab(widg, widg.objectName()[11:].capitalize())

        # _______________________________________BUTTONS_LAYER__________________________________
        self.label_finder = QtWidgets.QLabel()
        self.label_finder.setMaximumWidth(90)
        self.label_finder.setStyleSheet(stylesheet.label_finder)
        self.label_finder.setText('Поиск')

        self.lnedit_finder = QtWidgets.QLineEdit()
        self.lnedit_finder.setStyleSheet(stylesheet.line_edit)
        self.lnedit_finder.setPlaceholderText('Поиск')
        self.lnedit_finder.textChanged.connect(self.btn_finder_clicked)
        self.lnedit_finder.setMaximumWidth(500)

        self.btn_finder = QtWidgets.QPushButton()
        self.btn_finder.setStyleSheet(stylesheet.button_general)
        self.btn_finder.setText('Додати Закупку')
        self.btn_finder.clicked.connect(self.add_purchase)

        self.btn_new_row = QtWidgets.QPushButton()
        self.btn_new_row.setStyleSheet(stylesheet.button_general)
        self.btn_new_row.setText('Додати Товар')
        self.btn_new_row.clicked.connect(self.btn_new_row_clicked)

        self.btn_save_all = QtWidgets.QPushButton()
        self.btn_save_all.setStyleSheet(stylesheet.button_general)
        self.btn_save_all.setText('2')
        self.btn_save_all.clicked.connect(self.btn_save_clicked)

        self.btn_show_all = QtWidgets.QPushButton()
        self.btn_show_all.setStyleSheet(stylesheet.button_general)
        self.btn_show_all.setText('3')
        self.btn_show_all.clicked.connect(self.btn_show_all_clicked)

        self.btn_delete_row = QtWidgets.QPushButton()
        self.btn_delete_row.setStyleSheet(stylesheet.button_delete)
        self.btn_delete_row.setText('Видалити')
        self.btn_delete_row.clicked.connect(self.btn_delete_row_clicked)

        # __________________________________TEXT_LAYER_________________________
        self.text_widget = TextWidget()
        # self.text_widget.setMaximumHeight(90)
        self.text_widget.cursorPositionChanged.connect(self.change_cell_text)
        self.text_widget.setAcceptRichText(False)
        self.text_widget.setStyleSheet(stylesheet.text_edit)

        self.label_info = QtWidgets.QLabel()
        self.label_info.setText('К-ть рядків: \n\n\nДата редагування: \n')
        self.label_info.setStyleSheet(stylesheet.label_info)

        self.lnedit_date = QtWidgets.QLineEdit()
        self.lnedit_date.setStyleSheet(stylesheet.line_edit)
        self.lnedit_date.setPlaceholderText('date')
        self.lnedit_date.returnPressed.connect(self.change_date_value)
        self.lnedit_date.setMaximumWidth(120)

    def layout_setup(self):
        # ________________________________BUTTONS_LAYOUT___________________________________
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setContentsMargins(10, 10, 300, 10)
        # buttons_layout.setSpacing(10)

        buttons_layout.addWidget(self.label_finder)
        buttons_layout.addWidget(self.lnedit_finder)
        buttons_layout.addWidget(self.btn_finder)
        buttons_layout.addWidget(self.btn_new_row)
        buttons_layout.addWidget(self.btn_save_all)
        buttons_layout.addWidget(self.btn_show_all)
        buttons_layout.addWidget(self.btn_delete_row)

        # ________________________________TEXTWIDGET_LAYOUT___________________________________
        text_edit_layout = QtWidgets.QHBoxLayout()
        text_edit_layout.setContentsMargins(0, 10, 300, 10)

        label_date_layout = QtWidgets.QVBoxLayout()
        label_date_layout.addWidget(self.lnedit_date)
        label_date_layout.addWidget(self.label_info)

        text_edit_layout.addLayout(label_date_layout)
        text_edit_layout.addWidget(self.text_widget)

        # ________________________________MAIN_LAYOUT___________________________________________
        top_layout_widget = QtWidgets.QWidget()
        top_layout_widget.setLayout(text_edit_layout)
        main_layout = QtWidgets.QVBoxLayout()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(top_layout_widget)
        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([125, 150])

        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(splitter)

        main_layout_widget = QtWidgets.QWidget()
        main_layout_widget.setLayout(main_layout)

        self.setCentralWidget(main_layout_widget)

    # __________________________________ LOGIC _______________________________________
    def add_purchase(self):
        try:
            row = self.get_linked_cell()[0]
            goods_id = self.model_goods.data(self.model_goods.index(row, 0))
            dbConnector.insert_into_purchase(goods_id)
            self.tab_widget.setCurrentIndex(1)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "goods"', exception=ex)



    def add_order(self):
        print('Добавление заказа')

    def get_stats(self):
        print('Таблица статистики')

    def cell_highlighted(self, current, previous):
        current_row, current_col = current.row(), current.column()
        self.text_widget.link_cell((current_row, current_col))
        print(self.text_widget.get_linked_cell())
        # меняем текст в виджете
        self.change_text_widget(current_row, current_col)
        self.draw_label_info(current_row)
        # self.label_cell_change(current_row, current_col)

        self.check_lsukr(previous.row(), previous.column())

    def check_lsukr(self, row, col):
        cell_value = self.model_goods.data(self.model_goods.index(row, col))
        current_row = row
        # создаем список всех LSUKR и сравниваем есть ли уже такой как в измененной ячейке
        lsukr_list = [self.model_goods.data(self.model_goods.index(row, 1)) for row in
                      range(self.model_goods.rowCount())
                      if row != current_row]
        if cell_value in lsukr_list:
            self.btn_show_all_clicked()

    def draw_label_info(self, row):
        date_record = self.model_goods.data(self.model_goods.index(row, 0))
        self.lnedit_date.setText(str(date_record))
        self.label_info.setText(f'К-ть рядків: \n{self.model_goods.rowCount()}\n\nДата редагування: \n{date_record}')

    def change_date_edit(self):
        pass

    def change_text_widget(self, row, col):
        text = self.model_goods.data(self.model_goods.index(row, col))
        self.text_widget.setText(str(text))

    def get_linked_cell(self):
        return self.text_widget.get_linked_cell()

    def change_cell_text(self):
        text = self.text_widget.toPlainText()
        linked_cell = self.get_linked_cell()
        if linked_cell:
            row, col = linked_cell
            self.model_goods.setData(self.model_goods.index(row, col), text)

    def change_date_value(self):
        date = self.lnedit_date.text()
        linked_cell = self.get_linked_cell()
        if linked_cell:
            row = linked_cell[0]
            self.model_goods.setData(self.model_goods.index(row, 5), date)
            self.draw_label_info(row)

    def filter_model(self, s):
        self.model_goods.setFilter(s)

    def btn_finder_clicked(self):
        text = self.lnedit_finder.text()
        text_safe = re.sub(r'\"+', '', text)  #substitute \'-symbol
        filtered_string = 'name LIKE "%{}%"'.format(text_safe)
        self.filter_model(filtered_string)

    def btn_new_row_clicked(self):
        operation_res = dbConnector.insert_into_goods()
        if operation_res[0] == 'Success':
            self.btn_show_all_clicked()
        elif operation_res[0] == 'integrity_error':
            self.draw_new_line_error_message(operation_res[1])
        elif operation_res[0] is False:
            self.draw_general_error_message(operation_res[1])

    def draw_new_line_error_message(self, exception_message):
        error_msg = QtWidgets.QMessageBox()
        error_msg.setWindowTitle('Помилка бази даних')
        error_msg.setText('Неможливо створити новий рядок тому,\nщо є попередній з незаповеним LSUKR')
        error_msg.setInformativeText(f'{exception_message}')
        error_msg.setIcon(QtWidgets.QMessageBox.Critical)

        error_msg.exec_()

    def draw_general_error_message(self, exception_message):
        generalDB_error_msg = QtWidgets.QMessageBox()
        generalDB_error_msg.setWindowTitle('Помилка бази даних')
        generalDB_error_msg.setText(f'Помилка в роботі з базою даних')
        generalDB_error_msg.setInformativeText(f'{exception_message}')

        generalDB_error_msg.exec_()

    def draw_error_message(self, error_text, exception:Exception='Undefined'):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Щось пішло не так =(')
        msg.setText(error_text)
        msg.setInformativeText(f'{exception}')

        msg.exec_()

    def btn_show_all_clicked(self):
        self.lnedit_finder.setText('')
        self.btn_finder_clicked()

    def btn_delete_row_clicked(self):
        indexes = self.table_view_goods.selectionModel().selectedRows()
        row_id = None
        for index in sorted(indexes):
            row_id = self.model_goods.data(self.model_goods.index(index.row(), 0))

        self.delete_row(row_id)

    def delete_row(self, row_id):
        dbConnector.delete_row(row_id, dbConnector.TABLE_GOODS)
        self.btn_show_all_clicked()

    def btn_save_clicked(self):
        print('Кнопка СОхранения')

    def setup_ui(self):
        self.setWindowTitle('Table Main Window')
        self.setMinimumSize(1000, 600)
        # self.setStyleSheet('background-color: #fcfee2;')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    mainWindow = TableWindow()
    mainWindow.show()

    sys.exit(app.exec_())
