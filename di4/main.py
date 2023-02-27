import re
import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QModelIndex

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

class DataOperator:
    def __init__(self):
        self.cell_coords = None
        self.model_list = []
        self.active_table = None

    def get_cell_coords(self):
        return self.cell_coords

    def set_sell_coords(self, coords: tuple):
        self.cell_coords = coords

    def get_active_table(self):
        return self.active_table

    def set_active_table(self, table:QtWidgets.QTableView):
        self.active_table = table


class TableWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(TableWindow, self).__init__()

        self.setup_ui()
        self.data_cash = DataOperator()
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

        self.data_cash.active_table = self.tab_widget.currentWidget()

    def model_create(self, table, headers, model_name):
        model = sql_pyqt.QSqlTableModel(db=sql_pyqt.db)
        model.setTable(table)
        model.setEditStrategy(sql_pyqt.QSqlTableModel.EditStrategy.OnFieldChange)
        model.sort(0, Qt.SortOrder.DescendingOrder)
        for i, name in enumerate(headers):
            model.setHeaderData(i + 1, Qt.Orientation.Horizontal, name)

        model.select()
        setattr(self, model_name, model)
        self.data_cash.model_list.append(getattr(self, model_name))

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
        # ____________________________________ TAB WIDGET SETUP _________________________
        self.tab_widget = QtWidgets.QTabWidget()
        tab_widgets_list = [self.table_view_goods, self.table_view_purchase, self.table_view_orders,
                            self.table_view_stat]
        for widg in tab_widgets_list:
            self.tab_widget.addTab(widg, widg.objectName()[11:].capitalize())
        self.tab_widget.currentChanged.connect(self.tab_changed)


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

        self.lnedit_id = QtWidgets.QLineEdit()
        self.lnedit_id.setStyleSheet(stylesheet.line_edit)
        self.lnedit_id.setPlaceholderText('date')
        self.lnedit_id.returnPressed.connect(self.change_date_value)
        self.lnedit_id.setMaximumWidth(120)

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
        label_date_layout.addWidget(self.lnedit_id)
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

# _____________________________________ SIGNALS/ACTIONS ___________________________________________
    def tab_changed(self, i):
        self.data_cash.set_active_table(self.tab_widget.widget(i))
        self.refresh_table(i)

    def cell_highlighted(self, current):
        # setting active cell coords
        #в будущем попробовать работаь с обьектом ячейки, а не с координатами
        row, col = current.row(), current.column()
        self.text_widget.link_cell((row, col))
        self.data_cash.set_sell_coords((row, col))

        print(self.data_cash.active_table.model().index(row,col).data())
        # меняем текст в виджете
        self.change_text_widget(row, col)
        self.draw_label_info(row)

    # __________________________________ LOGIC _______________________________________
    def add_purchase(self):
        try:
            row = self.get_linked_cell()[0]
            goods_id = self.model_goods.data(self.model_goods.index(row, 0))
            dbConnector.insert_into_purchase(goods_id)
            self.tab_widget.setCurrentIndex(1)
            current_amount = self.model_goods.data(self.model_goods.index(row, 2))
            self.model_goods.setData(self.model_goods.index(row, 2), current_amount + 1)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "goods"', exception=ex)



    def refresh_table(self, i):
        if i <= 2:
            self.data_cash.get_active_table().model().select()


    def add_order(self):
        print('Добавление заказа')

    def get_stats(self):
        print('Таблица статистики')


    def draw_label_info(self, row):
        model = self.data_cash.active_table.model()
        row_id = model.index(row, 0).data()
        # self.lnedit_id.setText(str(row_id))
        self.label_info.setText(f'К-ть рядків: \n{model.rowCount()}\n\nID рядку: \n{row_id}')

    def change_date_edit(self):
        pass

    def change_text_widget(self, row, col):
        #todo переделать под задачи
        model = self.data_cash.active_table.model()
        text = model.index(row, col).data()
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
        date = self.lnedit_id.text()
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
