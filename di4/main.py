import re
import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from di4 import dbConnector
from di4.settings import sql_pyqt
from di4.settings.Constants import (VALIDATOR_DIGITS,
                                    BASE_QUERY_ORDERS_ALL,
                                    BASE_TOTAL_PURCHASES,
                                    BASE_TOTAL_ORDERS)
from di4.static import stylesheet
from di4.settings import MyExceptions
from di4.settings.functors import QueryMaker, QueryMakerGroup


from di4.settings.backuper import write_backup

write_backup()


HEADERS_GOODS = ['Name', 'amount']
HEADERS_ORDERS = ['Name', 'sell_price', 'date']
HEADERS_PURCHASE = ['Name', 'buy_price', 'date']
HEADERS_STAT = ['Name', 'buy_price', 'sell_price', 'buy_date', 'sell_date']

INIT_NOW_DATE = dbConnector.NOW_DATE.strftime('%Y-%m')

TABLE_NAMES_LIST = [dbConnector.TABLE_GOODS, dbConnector.TABLE_PURCHASE, dbConnector.TABLE_ORDERS]


# TODO переделать способ формирования списка, потому что происходит дублирование массива
goods_names: list = []


def update_goods_names():
    global goods_names
    goods_names = [g[0] for g in dbConnector.select_goods_name()]


update_goods_names()

goods_completer = QtWidgets.QCompleter(goods_names)
goods_completer.setCaseSensitivity(Qt.CaseInsensitive)


def update_goods_completer():
    update_goods_names()
    global goods_completer
    goods_completer = QtWidgets.QCompleter(goods_names)
    goods_completer.setCaseSensitivity(Qt.CaseInsensitive)


class AddWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        update_goods_names()

        self.widgets_setup()
        self.layout_setup()

        self.properties_setup()

    def widgets_setup(self):
        self.add_button = QtWidgets.QPushButton()
        self.add_button.setText('Додати всі')

        self.field_price = QtWidgets.QLineEdit()
        self.field_price.setPlaceholderText('USD')
        self.field_price.setValidator(VALIDATOR_DIGITS)

        self.field_amount = QtWidgets.QLineEdit()
        self.field_amount.setPlaceholderText('к-ть')
        self.field_amount.setValidator(VALIDATOR_DIGITS)

        self.field_date = QtWidgets.QLineEdit()
        self.field_date.setPlaceholderText('yyyy-mm-dd')
        self.field_date.setText(dbConnector.NOW_DATE.strftime('%Y-%m-%d'))

        self.combox_goods_names = QtWidgets.QComboBox()
        self.combox_goods_names.setEditable(True)


    def layout_setup(self):
        layout_left = QtWidgets.QVBoxLayout()
        layout_left.addWidget(self.field_amount)
        layout_left.addWidget(self.field_price)
        layout_left.addWidget(self.field_date)

        layout_central = QtWidgets.QVBoxLayout()
        layout_central.addWidget(self.combox_goods_names)

        layout_right = QtWidgets.QVBoxLayout()
        layout_right.addWidget(self.add_button)

        layout_main = QtWidgets.QHBoxLayout()

        layout_main.addLayout(layout_left,7)
        layout_main.addLayout(layout_central,5)
        layout_main.addLayout(layout_right,3)

        self.setLayout(layout_main)

    def properties_setup(self):
        self.update_combobox_names()
        self.refresh_completer()

    def refresh_completer(self):
        self.combox_goods_names.setCompleter(goods_completer)

    def get_field_data(self):
        '''
        :return: goods_name, price, amount, date
        '''
        goods_name = self.combox_goods_names.currentText()
        date = self.field_date.text()
        amount = int(self.field_amount.text())
        price = float(self.field_price.text())
        return goods_name, price, amount, date

    def update_combobox_names(self):
        self.combox_goods_names.clear()
        self.combox_goods_names.addItems(goods_names)


class DataOperator:
    def __init__(self):
        self.cell_info = {'index': None, 'model': None}
        self.model_list:list = []

    def get_cell_info(self, key):
        return self.cell_info.get(key)

    def set_cell_info(self, index, model):
        self.cell_info['index'] = index
        self.cell_info['model'] = model


class TableWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

        self.query_makers_setup()
        self.data_cash = DataOperator()

        self.model_create(dbConnector.TABLE_GOODS, HEADERS_GOODS, 'model_goods')
        self.model_create(dbConnector.TABLE_PURCHASE, HEADERS_PURCHASE, 'model_purchase')

        # ************************* TEST CODE ****************************
        self.model_orders = sql_pyqt.QSqlQueryModel()
        query = sql_pyqt.QSqlQuery(self.orders_query.get_full_query(), db=sql_pyqt.db)
        self.model_orders.setQuery(query)
        for i, name in enumerate(HEADERS_ORDERS):
            self.model_orders.setHeaderData(i + 1, Qt.Orientation.Horizontal, name)
        # ************************** END TEST CODE *******************************

        self.create_table_view(getattr(self,'model_goods'), 'table_view_goods')
        self.create_table_view(getattr(self,'model_purchase'), 'table_view_purchase')
        self.create_table_view(getattr(self,'model_orders'), 'table_view_orders')
        self.table_view_setup()
        self.widgets_setup()
        self.layout_setup()

        self.lock_list = [self.btn_set_sell_date, self.btn_set_sell_price]


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

    def query_makers_setup(self):
        self.goods_query = QueryMaker('goods')
        self.goods_query.set_WHERE_fields({'name':''})

        self.purchase_query = QueryMaker('purchase')
        self.purchase_query.set_WHERE_fields({'purchase.date':INIT_NOW_DATE, 'name':''})

        self.orders_query = QueryMaker('orders',BASE_QUERY_ORDERS_ALL)
        self.orders_query.set_WHERE_fields({'orders.date':INIT_NOW_DATE, 'name':''})
        self.orders_query.set_ORDER_BY_fields('orders.id', ascending=False)

        self.purchase_query_grouped = QueryMakerGroup('purchase', 'goods.id', BASE_TOTAL_PURCHASES)
        self.purchase_query_grouped.set_WHERE_fields({'purchase.date': '2023-03', 'name': ''})
        self.purchase_query_grouped.set_ORDER_BY_fields('name')

        self.orders_query_grouped = QueryMakerGroup('orders', 'goods.name', BASE_TOTAL_ORDERS)
        self.orders_query_grouped.set_WHERE_fields({'name': '', 'orders.date': '2023-03'})
        self.orders_query_grouped.set_ORDER_BY_fields('name')


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
        self.tab_widget.setStyleSheet('font-size: 15px;')
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
        self.lnedit_finder.setCompleter(goods_completer)
        self.lnedit_finder.returnPressed.connect(self.lnedit_finder_pressed)
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
        self.btn_statistics_purchase.setStyleSheet('background-color: #f0776e;')
        self.btn_statistics_purchase.clicked.connect(self.btn_statistics_purchase_clicked)

        self.btn_statistics_order = QtWidgets.QPushButton()
        self.btn_statistics_order.setText('Orders Stat')
        self.btn_statistics_order.setStyleSheet('background-color: #bfed61;')
        self.btn_statistics_order.clicked.connect(self.btn_statistics_order_clicked)


        # __________________________________TEXT_LAYER_________________________
        self.label_info = QtWidgets.QLabel()
        self.label_info.setText('id=???')
        self.label_info.setStyleSheet(stylesheet.label_info)

        self.date_filter = QtWidgets.QLineEdit()
        self.date_filter.setStyleSheet(stylesheet.line_edit)
        self.date_filter.setPlaceholderText('yyyy-mm')
        self.date_filter.setText(INIT_NOW_DATE)
        self.date_filter.setMaximumWidth(120)
        self.date_filter.returnPressed.connect(self.date_filter_pressed)

        self.checkbox_date_filter = QtWidgets.QCheckBox('On')
        self.checkbox_date_filter.setChecked(True)
        ch_box = self.checkbox_date_filter
        ch_box.clicked.connect(lambda: ch_box.setText('On') if ch_box.isChecked() else ch_box.setText('Off'))
        ch_box.clicked.connect(
            lambda: self.date_filter.setEnabled(True) if ch_box.isChecked() else self.date_filter.setEnabled(False))
        ch_box.clicked.connect(self.checkbox_filter_clicked)

        self.lbl_quick_stat_buy = QtWidgets.QLabel()
        self.lbl_quick_stat_buy.setText('buy_total: \n__ ')

        self.lbl_quick_stat_sell = QtWidgets.QLabel()
        self.lbl_quick_stat_sell.setText('sell_total: \n__ ')


        # ____________________________________ MODELS _________________________________
        self.model_purchase.setRelation(1, sql_pyqt.QSqlRelation("goods", 'id', 'name'))


    def layout_setup(self):
        # ________________________________BUTTONS_LAYOUT___________________________________
        buttons_layout = QtWidgets.QHBoxLayout()

        buttons_layout.addWidget(self.lnedit_finder)
        buttons_layout.addWidget(self.btn_new_goods)
        buttons_layout.addWidget(self.btn_new_purchase)
        buttons_layout.addWidget(self.btn_new_order)
        buttons_layout.addWidget(self.btn_delete_row)
        buttons_layout.addWidget(self.btn_add_many_purchases)

        # ________________________________EDIT WIDGETS_LAYOUT___________________________________
        properties_layout = QtWidgets.QHBoxLayout()

        label_date_layout = QtWidgets.QVBoxLayout()
        label_date_layout.addWidget(self.date_filter)
        label_date_layout.addWidget(self.checkbox_date_filter)
        label_date_layout.addWidget(self.label_info)

        stats_layout = QtWidgets.QVBoxLayout()
        stats_layout.addWidget(self.lbl_quick_stat_buy)
        stats_layout.addWidget(self.lbl_quick_stat_sell)

        properties_layout.addLayout(label_date_layout)
        properties_layout.addLayout(stats_layout)
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
    def date_filter_pressed(self):
        self.update_date_filters()
        self.activate_filter()

    def lnedit_finder_pressed(self):
        self.update_name_filters()
        self.activate_filter()

    def checkbox_filter_clicked(self):
        self.update_date_filters()
        self.activate_filter()

    def btn_new_goods_clicked(self):
        self.action_add_new_goods()
        self.refresh_table(0)
        self.tab_widget.setCurrentIndex(0)

    def btn_add_many_purchases_clicked(self):
        update_goods_completer()
        self.window_add_many_purchases.update_combobox_names()
        self.window_add_many_purchases.refresh_completer()
        self.window_add_many_purchases.show()

    def btn_statistics_purchase_clicked(self):
        if self.checkbox_date_filter.isChecked():
            query = self.purchase_query_grouped.get_full_query_grouped('purchase.date', 'name')
        else:
            query = self.purchase_query_grouped.get_full_query_grouped('name')
        self.show_stat_table(query)
        self.calculate_statistic_buy(query)

    def btn_statistics_order_clicked(self):
        if self.checkbox_date_filter.isChecked():
            query = self.orders_query_grouped.get_full_query_grouped('orders.date', 'name')

        else:
            query = self.orders_query_grouped.get_full_query_grouped('name')
        self.show_stat_table(query)
        self.calculate_statistic_sell(query)

    def calculate_statistic_buy(self, query_inner):
        query = f'''SELECT SUM(buy_total) FROM ({query_inner[:-1]})'''
        res = dbConnector.select_execution(query)
        self.draw_quick_stat_buy(res[0][0])

    def calculate_statistic_sell(self, query_inner):
        query = f'''SELECT SUM(sell_total) FROM ({query_inner[:-1]})'''
        res = dbConnector.select_execution(query)
        self.draw_quick_stat_sell(res[0][0])


    def tab_changed(self, i):
        #TODO нужно передать функцию. Отрефакторить или вообще поменять подход

        # self.lnedit_finder.clear()
        self.refresh_completer()
        self.refresh_table(i)
        self.lock_widgets(self.lock_list)
        if i == 2:
            self.unlock_widgets(self.lock_list)

    def cell_highlighted(self, current):
        row, col = current.row(), current.column()
        self.data_cash.set_cell_info(current, self.tab_widget.currentWidget().model())

        # меняем текст в виджете
        self.draw_on_label_info(row)

    def btn_delete_row_clicked(self):
        row_id = self.label_info.text().split('=')[1].strip()
        current_table_index = self.tab_widget.currentIndex()
        try:
            if current_table_index > 2:
                raise MyExceptions.GeneralException('Видаляти можна тільки в перших трьох таблицях!\n'
                                                    'І то, краще вообще не видаляти')
            if not row_id.isdigit():
                raise MyExceptions.GeneralException('Оберіть рядок для видалення')
            self.delete_row(row_id,current_table_index)

        except Exception as ex:
            self.draw_error_message('Шось не то =(', exception=ex)

    def btn_update_sell_price_clicked(self):
        price_str = self.lnedit_sell_price.text()
        if price_str:
            price = float(price_str)
            self.edit_order_cell(dbConnector.update_order_price, price)

    def btn_update_sell_date_clicked(self):
        self.edit_order_cell(dbConnector.update_order_date, self.lnedit_date_order.text())

    # __________________________________ SLOTS _____________________________________________
    def activate_filter(self):
        table_index = self.tab_widget.currentIndex()
        if  table_index == 0:
            self.activate_filter_goods()
        elif table_index == 1:
            self.activate_filter_purchase()
        elif table_index == 2:
            self.activate_filter_orders()

    def draw_quick_stat_sell(self, text):
        self.lbl_quick_stat_sell.setText(f'sell-total: \n{text}')

    def draw_quick_stat_buy(self, text):
        self.lbl_quick_stat_buy.setText(f'buy_total: \n{text}')

    def activate_filter_goods(self):
        self.model_goods.setFilter(self.goods_query.get_WHERE_filter('name'))

    def activate_filter_purchase(self):
        if self.checkbox_date_filter.isChecked():
            self.model_purchase.setFilter(self.purchase_query.get_WHERE_filter('name', 'purchase.date'))
        else:
            self.model_purchase.setFilter(self.purchase_query.get_WHERE_filter('name'))

    def activate_filter_orders(self):
        if self.checkbox_date_filter.isChecked():
            orders_query = self.orders_query.get_full_query('name', 'orders.date')
        else:
            orders_query = self.orders_query.get_full_query('name')

        self.model_orders.setQuery(sql_pyqt.QSqlQuery(orders_query, db=sql_pyqt.db))

    def update_name_filters(self):
        name = self.make_safe_filter_string(self.lnedit_finder.text())
        # TODO отрефакторить через цикл
        self.goods_query.set_WHERE_fields({'name': name})
        self.purchase_query.set_WHERE_fields({'name': name})
        self.orders_query.set_WHERE_fields({'name': name})
        self.purchase_query_grouped.set_WHERE_fields({'name':name})
        self.orders_query_grouped.set_WHERE_fields({'name':name})

    def update_date_filters(self):
        # TODO тоже отрефакторить через цикл
        date = self.make_safe_filter_string(self.date_filter.text())
        self.orders_query.set_WHERE_fields({'orders.date': date})
        self.purchase_query.set_WHERE_fields({'purchase.date': date})
        self.purchase_query_grouped.set_WHERE_fields({'purchase.date': date})
        print(date)
        self.orders_query_grouped.set_WHERE_fields({'orders.date': date})

    def refresh_completer(self):
        update_goods_completer()
        self.lnedit_finder.setCompleter(goods_completer)

    @staticmethod
    def lock_widgets(widgets: list):
        for widget in widgets:
            widget.setDisabled(True)

    @staticmethod
    def unlock_widgets(widgets: list):
        for widget in widgets:
            widget.setDisabled(False)

    def refresh_table(self, table_index):
        #todo сделать перегрузку функции
        if table_index <= 1:
            self.tab_widget.currentWidget().model().select()

        elif table_index == 2:
            self.activate_filter_orders()


    def get_active_cell_index(self):
        return self.data_cash.get_cell_info('index')

    def get_active_cell_model(self):
        return self.data_cash.get_cell_info('model')

    # __________________________________ LOGIC _______________________________________
    def action_add_many_purchases(self):
        name, price,amount,date = self.window_add_many_purchases.get_field_data()
        self.add_many_purchases(name,price,amount,date)

        self.tab_widget.setCurrentIndex(1)

    def show_stat_table(self, base_query):
        query = sql_pyqt.QSqlQuery(base_query, db=sql_pyqt.db)
        model = sql_pyqt.QSqlQueryModel()
        model.setQuery(query)
        self.table_view_stat.setModel(model)
        self.tab_widget.setCurrentIndex(3)

    def delete_row(self, row_id, table_index):
        if table_index == 0:
            dbConnector.delete_row(row_id, TABLE_NAMES_LIST[table_index])
        elif table_index == 1:
            query = f'''WHERE id = (SELECT goods_id FROM purchase WHERE id = {row_id})'''

        self.refresh_table(table_index)


    def get_goods_id(self, goods_name):
        try:
            return dbConnector.select_goods_id(goods_name)[0][0]
        except IndexError as ex:
            self.draw_error_message('Такого товару не знайдено =(', exception=ex)

    def add_many_purchases(self, goods_name, price, amount, date):
        goods_id = self.get_goods_id(goods_name)
        if goods_id:
            try:
                for i in range(amount):
                    dbConnector.insert_into_purchase(goods_id, price, date)
                current_amount = dbConnector.select_goods_amount(goods_id)[0][0]
                dbConnector.update_goods_amount(goods_id, current_amount+amount)
                self.refresh_table(1)
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

    def edit_order_cell(self, db_func, value):
        try:
            order_id = int(self.label_info.text().split('=')[1].strip())
            db_func(order_id, value)
            self.refresh_table(2)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "orders"', exception=ex)

    def draw_on_label_info(self, row):
        model = self.tab_widget.currentWidget().model()
        self.label_info.setText(f'obj_id = {model.index(row, 0).data()}')

    @staticmethod
    def make_safe_filter_string(text):
        text_safe = re.sub(r'\"+', '', text.strip())
        return text_safe

    def action_add_new_goods(self):
        dbConnector.insert_into_goods()

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

    def setup_ui(self):
        self.setWindowTitle('Table Main Window')
        self.setMinimumSize(1000, 600)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    mainWindow = TableWindow()
    mainWindow.show()

    sys.exit(app.exec_())
