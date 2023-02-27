import datetime
import re
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

import dbConnector
from di4.settings import sql_pyqt
from di4.static import stylesheet
from di4.settings import MyExceptions

HEADERS_GOODS = ['Name', 'amount']
HEADERS_ORDERS = ['Name', 'sell_price', 'date']
HEADERS_PURCHASE = ['Name', 'buy_price', 'date']
HEADERS_STAT = ['Name', 'buy_price', 'sell_price', 'buy_date', 'sell_date']

VALIDATOR_DIGITS = QtGui.QRegExpValidator(QtCore.QRegExp(r'[0-9.]+'))

query_all_orders = '''
        SELECT orders.id, goods.name, sell_price, orders.date 
        FROM orders 
        JOIN purchase ON purchase.id = orders.purchase_id
        JOIN goods ON goods.id = purchase.goods_id
        ORDER BY orders.id DESC;'''

query_total_purchases = '''
        SELECT name, SUM(buy_price) as summa
        FROM purchase 
        JOIN goods ON purchase.goods_id = goods.id
        GROUP BY goods_id;'''

query_total_orders = '''
        SELECT goods.name, sum(sell_price) as summa
        FROM orders 
        JOIN purchase ON purchase.id = orders.purchase_id
        JOIN goods ON goods.id = purchase.goods_id
        GROUP BY goods.name
        ORDER BY orders.id DESC;'''


TABLE_NAMES_LIST = [dbConnector.TABLE_GOODS, dbConnector.TABLE_PURCHASE, dbConnector.TABLE_ORDERS]


class AddWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.widgets_setup()
        self.layout_setup()

        self.goods_names_list = []

    def widgets_setup(self):
        self.add_button = QtWidgets.QPushButton()
        self.add_button.setText('Додати всі')

        self.field_price = QtWidgets.QLineEdit()
        self.field_price.setPlaceholderText('USD')
        self.field_price.setValidator(VALIDATOR_DIGITS)

        self.field_amount =QtWidgets.QLineEdit()
        self.field_amount.setPlaceholderText('к-ть')
        self.field_amount.setValidator(VALIDATOR_DIGITS)

        self.field_date = QtWidgets.QLineEdit()
        self.field_date.setPlaceholderText('yyyy-mm-dd')
        self.field_date.setText(dbConnector.NOW_DATE.strftime('%Y-%m-%d'))

        self.combox_goods_names = QtWidgets.QComboBox()
        self.update_combobox_names()

    def layout_setup(self):
        layout_left = QtWidgets.QVBoxLayout()
        layout_left.addWidget(self.field_amount)
        layout_left.addWidget(self.field_price)
        layout_left.addWidget(self.field_date)

        layout_right = QtWidgets.QVBoxLayout()
        layout_right.addWidget(self.add_button)
        layout_right.addWidget(self.combox_goods_names)

        layout_main = QtWidgets.QHBoxLayout()

        layout_main.addLayout(layout_left,7)
        layout_main.addLayout(layout_right,3)

        self.setLayout(layout_main)

    def get_field_data(self):
        '''
        :return: goods_name, price, amount, date
        '''
        goods_name = self.combox_goods_names.currentText()
        date = self.field_date.text()
        amount = int(self.field_amount.text())
        price = float(self.field_price.text())
        return goods_name, price, amount, date

    def load_goods_list(self):
        self.goods_names_list = [g[0] for g in dbConnector.select_goods_name()]

    def update_combobox_names(self):
        self.load_goods_list()
        self.combox_goods_names.clear()
        self.combox_goods_names.addItems(self.goods_names_list)


class DataOperator:
    def __init__(self):
        self.cell_info = {'index': None, 'model': None}
        self.model_list:list = []
        self.active_table:QtWidgets.QTableView = None

    def get_cell_info(self, key):
        return self.cell_info.get(key)

    def set_cell_info(self, index, model):
        self.cell_info['index'] = index
        self.cell_info['model'] = model

    def get_active_table(self):
        return self.active_table

    def set_active_table(self, table:QtWidgets.QTableView):
        self.active_table = table


class TableWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setup_ui()
        self.data_cash = DataOperator()
        self.model_create(dbConnector.TABLE_GOODS, HEADERS_GOODS, 'model_goods')
        self.model_create(dbConnector.TABLE_PURCHASE, HEADERS_PURCHASE, 'model_purchase')
        # self.model_create(dbConnector.TABLE_ORDERS, HEADERS_ORDERS, 'model_orders')

        # ************************* TEST CODE ****************************
        self.model_orders = sql_pyqt.QSqlQueryModel()
        query = sql_pyqt.QSqlQuery(query_all_orders, db=sql_pyqt.db)
        self.model_orders.setQuery(query)
        # self.model_orders.setEditStrategy(sql_pyqt.QSqlTableModel.EditStrategy.OnFieldChange)
        for i, name in enumerate(HEADERS_ORDERS):
            self.model_orders.setHeaderData(i + 1, Qt.Orientation.Horizontal, name)

        # ************************** END TEST CODE *******************************

        self.create_table_view(getattr(self,'model_goods'), 'table_view_goods')
        self.create_table_view(getattr(self,'model_purchase'), 'table_view_purchase')
        self.create_table_view(getattr(self,'model_orders'), 'table_view_orders')
        # self.create_table_view(getattr(self,'model_goods'), 'table_view_goods')
        # self.model_create(dbConnector.TABLE_PURCHASE,HEADERS_PURCHASE,'model_stat')
        self.table_view_setup()
        self.widgets_setup()
        self.layout_setup()

        self.data_cash.active_table = self.tab_widget.currentWidget()

    def model_create(self, table:str, headers:list, model_name:str):
        model = sql_pyqt.QSqlRelationalTableModel(db=sql_pyqt.db)
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
        self.table_view_purchase.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_orders.selectionModel().currentChanged.connect(self.cell_highlighted)


    def widgets_setup(self):
        # ____________________________________ TAB WIDGET SETUP _________________________
        self.tab_widget = QtWidgets.QTabWidget()
        tab_widgets_list = [self.table_view_goods, self.table_view_purchase, self.table_view_orders,
                            self.table_view_stat]
        for widg in tab_widgets_list:
            self.tab_widget.addTab(widg, widg.objectName()[11:].capitalize())
        self.tab_widget.currentChanged.connect(self.tab_changed)


        # _____________________________________ ADD WIDGET SETUP _______________________________
        self.window_add_many_purchases = AddWidget()
        self.window_add_many_purchases.add_button.clicked.connect(self.action_add_many_purchases)


        # _______________________________________BUTTONS_LAYER__________________________________
        self.lnedit_finder = QtWidgets.QLineEdit()
        self.lnedit_finder.setStyleSheet(stylesheet.line_edit)
        self.lnedit_finder.setPlaceholderText('Пошук')
        self.lnedit_finder.textChanged.connect(self.action_filtered_search)
        self.lnedit_finder.setMaximumWidth(500)

        self.btn_new_goods = QtWidgets.QPushButton()
        # self.btn_new_goods.setStyleSheet(stylesheet.button_general)
        self.btn_new_goods.setText('Додати Товар')
        self.btn_new_goods.clicked.connect(self.btn_new_goods_clicked)

        self.btn_new_purchase = QtWidgets.QPushButton()
        self.btn_new_purchase.setStyleSheet(stylesheet.button_general)
        self.btn_new_purchase.setText('Додати Закупку')
        self.btn_new_purchase.clicked.connect(self.add_purchase)

        self.btn_add_many_purchases = QtWidgets.QPushButton()
        self.btn_add_many_purchases.setStyleSheet('background-color: #c3c305;')
        self.btn_add_many_purchases.setText('Декілька Закупок')
        self.btn_add_many_purchases.clicked.connect(self.btn_add_many_purchases_clicked)


        self.btn_new_order = QtWidgets.QPushButton()
        self.btn_new_order.setStyleSheet(stylesheet.button_general)
        self.btn_new_order.setText('Додати продажу')
        self.btn_new_order.clicked.connect(self.add_order)

        self.btn_delete_row = QtWidgets.QPushButton()
        self.btn_delete_row.setStyleSheet(stylesheet.button_delete)
        self.btn_delete_row.setText('Видалити')
        self.btn_delete_row.clicked.connect(self.btn_delete_row_clicked)


    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ EDITING LAYER ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.lnedit_sell_price = QtWidgets.QLineEdit()
        self.lnedit_sell_price.setValidator(VALIDATOR_DIGITS)
        self.lnedit_sell_price.setPlaceholderText('USD')

        self.btn_set_sell_price = QtWidgets.QPushButton()
        self.btn_set_sell_price.setText('Змінити ціну продажу')
        self.btn_set_sell_price.setDisabled(True)
        self.btn_set_sell_price.clicked.connect(self.btn_update_sell_price_clicked)

        self.lnedit_date_order = QtWidgets.QLineEdit()
        self.lnedit_date_order.setPlaceholderText('yyyy-mm-dd')

        self.btn_set_sell_date = QtWidgets.QPushButton()
        self.btn_set_sell_date.setText('Змінити дату продажу')
        self.btn_set_sell_date.setDisabled(True)
        self.btn_set_sell_date.clicked.connect(self.btn_update_sell_date_clicked)

        self.btn_statistics_purchase = QtWidgets.QPushButton()
        self.btn_statistics_purchase.setText('Purchase Stat')
        self.btn_statistics_purchase.clicked.connect(self.btn_statistics_purchase_clicked)

        self.btn_statistics_order = QtWidgets.QPushButton()
        self.btn_statistics_order.setText('Orders Stat')
        self.btn_statistics_order.clicked.connect(self.btn_statistics_order_clicked)



        # __________________________________TEXT_LAYER_________________________
        self.label_info = QtWidgets.QLabel()
        self.label_info.setText('id=???')
        self.label_info.setStyleSheet(stylesheet.label_info)

        self.lnedit_id = QtWidgets.QLineEdit()
        self.lnedit_id.setStyleSheet(stylesheet.line_edit)
        self.lnedit_id.setPlaceholderText('---')
        self.lnedit_id.setMaximumWidth(120)

        # ____________________________________ MODELS _________________________________
        self.model_purchase.setRelation(1, sql_pyqt.QSqlRelation("goods", 'id', 'name'))


    def layout_setup(self):
        # ________________________________BUTTONS_LAYOUT___________________________________
        buttons_layout = QtWidgets.QHBoxLayout()
        # buttons_layout.setContentsMargins(10, 10, 300, 10)
        # buttons_layout.setSpacing(10)

        buttons_layout.addWidget(self.lnedit_finder)
        buttons_layout.addWidget(self.btn_new_goods)
        buttons_layout.addWidget(self.btn_new_purchase)
        buttons_layout.addWidget(self.btn_new_order)
        buttons_layout.addWidget(self.btn_delete_row)
        buttons_layout.addWidget(self.btn_add_many_purchases)

        # ________________________________EDIT WIDGETS_LAYOUT___________________________________
        properties_layout = QtWidgets.QHBoxLayout()

        label_date_layout = QtWidgets.QVBoxLayout()
        label_date_layout.addWidget(self.lnedit_id)
        label_date_layout.addWidget(self.label_info)

        properties_layout.addLayout(label_date_layout)
        properties_layout.addWidget(self.lnedit_sell_price,2)
        properties_layout.addWidget(self.btn_set_sell_price,3)
        properties_layout.addWidget(self.lnedit_date_order,4)
        properties_layout.addWidget(self.btn_set_sell_date,3)
        properties_layout.addWidget(self.btn_statistics_purchase, 3)
        properties_layout.addWidget(self.btn_statistics_order, 3)

        # ________________________________MAIN_LAYOUT___________________________________________
        top_layout_widget = QtWidgets.QWidget()
        top_layout_widget.setLayout(properties_layout)
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
    def btn_add_many_purchases_clicked(self):
        self.window_add_many_purchases.update_combobox_names()
        self.window_add_many_purchases.show()

    def action_add_many_purchases(self):
        name, price,amount,date = self.window_add_many_purchases.get_field_data()
        self.add_many_purchases(name,price,amount,date)

        self.tab_widget.setCurrentIndex(1)

    def btn_statistics_purchase_clicked(self):
        self.show_purchase_total_stat()

    def btn_statistics_order_clicked(self):
        self.show_orders_total_stat()

    def show_purchase_total_stat(self):
        #todo свести два метода в один
        query = sql_pyqt.QSqlQuery(query_total_purchases, db=sql_pyqt.db)
        model = sql_pyqt.QSqlQueryModel()
        model.setQuery(query)
        self.table_view_stat.setModel(model)
        self.tab_widget.setCurrentIndex(3)

    def show_orders_total_stat(self):
        query = sql_pyqt.QSqlQuery(query_total_orders, db=sql_pyqt.db)
        model = sql_pyqt.QSqlQueryModel()
        model.setQuery(query)
        self.table_view_stat.setModel(model)
        self.tab_widget.setCurrentIndex(3)


    def tab_changed(self, i):
        #TODO нужно передать функцию. Отрефакторить или вообще поменять подход
        self.data_cash.set_active_table(self.tab_widget.widget(i))
        self.refresh_table(i)
        lock_list = [self.btn_set_sell_date, self.btn_set_sell_price]
        self.lock_widgets(lock_list)
        if i == 2:
            self.unlock_widgets(lock_list)


    def cell_highlighted(self, current):
        row, col = current.row(), current.column()
        self.data_cash.set_cell_info(current, self.tab_widget.currentWidget().model())

        # меняем текст в виджете
        self.draw_label_info(row)

    def btn_show_all_clicked(self):
        self.lnedit_finder.setText('')

    def btn_delete_row_clicked(self):
        row_id = self.label_info.text().split('=')[1].strip()
        current_table_index = self.tab_widget.currentIndex()
        try:
            if not row_id.isdigit():
                raise MyExceptions.GeneralException('Оберіть рядок для видалення')
            self.delete_row(row_id,current_table_index)

        except Exception as ex:
            self.draw_error_message('Шось не то =(', exception=ex)


    def btn_update_sell_price_clicked(self):
        price_str = self.lnedit_sell_price.text()
        if price_str:
            price = float(price_str)
            self.update_sell_price(price)

    def btn_update_sell_date_clicked(self):
        self.update_sell_date()

    # __________________________________ LOGIC _______________________________________
    def lock_widgets(self, widgets:list):
        for widget in widgets:
            widget.setDisabled(True)

    def unlock_widgets(self, widgets:list):
        for widget in widgets:
            widget.setDisabled(False)

    def delete_row(self, row_id, table_index):
        dbConnector.delete_row(row_id, TABLE_NAMES_LIST[table_index])
        self.refresh_table(table_index)


    def refresh_table(self, i):
        #todo сделать перегрузку функции
        if i <= 1:
            self.tab_widget.currentWidget().model().select()
        elif i == 2:
            query = sql_pyqt.QSqlQuery(query_all_orders, db=sql_pyqt.db)
            self.model_orders.setQuery(query)

    def add_many_purchases(self, goods_name, price, amount, date):
        goods_id = dbConnector.select_goods_id(goods_name)[0][0]
        try:
            for i in range(amount):
                dbConnector.insert_into_purchase(goods_id, price, date)
            current_amount = dbConnector.select_goods_amount(goods_id)[0][0]
            dbConnector.update_goods_amount(goods_id, current_amount+amount)
        except Exception as ex:
            self.draw_error_message('Шось не то =(', exception=ex)

    def add_purchase(self):
        try:
            row = self.get_active_cell_index().row()
            goods_id = self.model_goods.index(row, 0).data()
            print(goods_id)
            if self.tab_widget.currentIndex() != 0:
                raise MyExceptions.GeneralException('Таблиця "goods" має бути активною')
            dbConnector.insert_into_purchase(goods_id)
            current_amount = self.model_goods.data(self.model_goods.index(row, 2))
            self.model_goods.setData(self.model_goods.index(row, 2), current_amount + 1)
            self.tab_widget.setCurrentIndex(1)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "goods"', exception=ex)

    def add_order(self):
        try:
            row = self.get_active_cell_index().row()
            purchase_id = self.model_purchase.index(row,0).data()
            purchase_status = self.model_purchase.index(row,4).data()
            print(purchase_id, purchase_status)
            if self.tab_widget.currentIndex() != 1:
                raise MyExceptions.GeneralException('Таблиця "purchase" має бути активною')
            if purchase_status == 0:
                raise MyExceptions.GeneralException('Цей товар вже продано!')
            dbConnector.insert_into_orders(purchase_id)
            self.model_purchase.setData(self.model_purchase.index(row,4), 0)
            self.tab_widget.setCurrentIndex(2)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "purchase"', exception=ex)


    def update_sell_date(self):
        date = self.lnedit_date_order.text()
        try:
            order_id = int(self.label_info.text().split('=')[1].strip())
            if self.tab_widget.currentIndex() != 2:
                raise MyExceptions.GeneralException('Таблиця "orders" має бути активною')
            print(date)
            dbConnector.update_order_date(order_id, date)
            self.refresh_table(2)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "orders"', exception=ex)

    def update_sell_price(self, price):
        try:
            order_id = int(self.label_info.text().split('=')[1].strip())
            if self.tab_widget.currentIndex() != 2:
                raise MyExceptions.GeneralException('Таблиця "orders" має бути активною')
            dbConnector.update_order_price(order_id,price)
            self.refresh_table(2)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "orders"', exception=ex)

    def get_stats(self):
        print('Таблица статистики')

    def draw_label_info(self, row):
        model = self.tab_widget.currentWidget().model()
        self.label_info.setText(f'obj_id = {model.index(row, 0).data()}')


    def get_active_cell_index(self):
        return self.data_cash.get_cell_info('index')

    def get_active_cell_model(self):
        return self.data_cash.get_cell_info('model')

    def filter_model(self, s):
        self.model_goods.setFilter(s)

    def action_filtered_search(self):
        text = self.lnedit_finder.text()
        text_safe = re.sub(r'\"+', '', text)  #substitute \'-symbol
        filtered_string = 'name LIKE "%{}%"'.format(text_safe)
        self.model_goods.setFilter(filtered_string)

    def btn_new_goods_clicked(self):
        dbConnector.insert_into_goods()
        self.refresh_table(0)
        self.tab_widget.setCurrentIndex(0)

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
