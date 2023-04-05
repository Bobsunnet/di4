import os
import re
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from di4 import dbConnector
from di4.settings import sql_pyqt
from di4.settings.Constants import (VALIDATOR_DIGITS,
                                    BASE_TOTAL_PURCHASES,
                                    BASE_TOTAL_ORDERS)
from di4.settings import MyExceptions
from di4.settings.functors import QueryMaker, QueryMakerGroup
from di4.settings.backuper import write_backup

write_backup()

BASEDIR = os.path.dirname(__file__)
STYLES_PATH = os.path.join(BASEDIR, 'static/style/style.css')

with open(STYLES_PATH, 'r') as file:
    style = file.read()


HEADERS_GOODS = ['Name', 'amount']
HEADERS_ORDERS = ['Name', 'sell_price', 'date']
HEADERS_PURCHASE = ['Name', 'buy_price', 'date']
HEADERS_STAT = ['Name', 'buy_price', 'sell_price', 'buy_date', 'sell_date']

INIT_NOW_MONTH = dbConnector.NOW_DATE.strftime('%Y-%m')
INIT_NOW_DAY = dbConnector.NOW_DATE.strftime('%Y-%m-%d')

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


class MyTableView(QtWidgets.QTableView):
    def __init__(self):
        super(MyTableView, self).__init__()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu)

    def right_menu(self, pos):
        menu = QtWidgets.QMenu()

        # Add menu options
        hello_option = menu.addAction('Add Purchase(in testing...)')
        goodbye_option = menu.addAction('Add Order(in testing...)')

        # Menu option events
        hello_option.triggered.connect(mainWindow.btn_add_purchase_clicked)
        goodbye_option.triggered.connect(mainWindow.btn_add_order_clicked)

        # Position
        menu.exec_(self.mapToGlobal(pos))


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
        self.field_price.setPlaceholderText('0.00')
        self.field_price.setValidator(VALIDATOR_DIGITS)

        self.field_amount = QtWidgets.QLineEdit()
        self.field_amount.setPlaceholderText('к-ть')
        self.field_amount.setValidator(VALIDATOR_DIGITS)

        self.field_date = QtWidgets.QLineEdit()
        self.field_date.setPlaceholderText('yyyy-mm-dd')
        self.field_date.setText(INIT_NOW_DAY)

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
        amount_field = self.field_amount.text()
        if not isinstance(amount_field, int):
            raise MyExceptions.InvalidDataField('Невірно заповнене поле')
        amount = int(amount_field)
        price = float(self.field_price.text()) if self.field_price.text() else 0
        return goods_name, price, amount, date

    def update_combobox_names(self):
        self.combox_goods_names.clear()
        self.combox_goods_names.addItems(goods_names)


class DataOperator:
    def __init__(self):
        self.cell_info = {}
        self.model_list:list = []
        self.selected_rows_ids = None

    def get_cell_info(self, key:str):
        """ :param key: info type(index or model) """
        return self.cell_info.get(key)

    def set_cell_info(self, index, model):
        self.cell_info['index'] = index
        self.cell_info['model'] = model

    def reset_cell_info(self):
        self.cell_info['index'] = None
        self.cell_info['model'] = None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.model_purchase = None
        self.model_orders = None
        self.setup_ui()

        self.query_makers_setup()
        self.data_cash = DataOperator()

        self.model_create(dbConnector.TABLE_GOODS, HEADERS_GOODS, 'model_goods')
        self.model_create(dbConnector.TABLE_PURCHASE, HEADERS_PURCHASE, 'model_purchase')
        self.model_create(dbConnector.TABLE_ORDERS, HEADERS_ORDERS, 'model_orders')

        self.table_view_setup()
        self.widgets_setup()
        self.layout_setup()
        self.tool_bar_setup()

    def tool_bar_setup(self):
        tool_bar = QtWidgets.QToolBar('Main toolbar')
        tool_bar.setIconSize(QtCore.QSize(16,16))
        self.addToolBar(tool_bar)

        self.act_debug = QtWidgets.QAction(QtGui.QIcon(f'{BASEDIR}/static/icons/bug.png'), 'debug', self)
        self.act_debug.triggered.connect(self.debug_action)
        self.act_add_many_purchases = QtWidgets.QAction('Кілька закупок')
        #todo сделать отдельным потоком это действие
        self.act_add_many_purchases.triggered.connect(self.btn_add_many_purchases_clicked)

        tool_bar.addAction(self.act_debug)
        tool_bar.addSeparator()
        tool_bar.addAction(self.act_add_many_purchases)

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
        table_view = MyTableView()
        table_view.setObjectName(obj_name)
        table_view.setModel(model)
        table_view.hideColumn(0)
        for i in range(model.columnCount() - 1):
            table_view.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        table_view.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        setattr(self, obj_name, table_view)

    def query_makers_setup(self):
        self.goods_query = QueryMaker('goods')
        self.goods_query.set_WHERE_fields({'name':''})

        self.purchase_query = QueryMaker('purchase')
        self.purchase_query.set_WHERE_fields({'purchase.date':INIT_NOW_MONTH, 'name': ''})

        self.orders_query = QueryMaker('orders')
        self.orders_query.set_WHERE_fields({'orders.date':INIT_NOW_MONTH, 'name': ''})
        self.orders_query.set_ORDER_BY_fields('orders.id', ascending=False)

        self.purchase_query_grouped = QueryMakerGroup('purchase', 'goods.id', BASE_TOTAL_PURCHASES)
        self.purchase_query_grouped.set_WHERE_fields({'purchase.date': '2023-03', 'name': ''})
        self.purchase_query_grouped.set_ORDER_BY_fields('name')

        self.orders_query_grouped = QueryMakerGroup('orders', 'goods.name', BASE_TOTAL_ORDERS)
        self.orders_query_grouped.set_WHERE_fields({'name': '', 'orders.date': '2023-03'})
        self.orders_query_grouped.set_ORDER_BY_fields('name')

    def table_view_setup(self):
        self.create_table_view(getattr(self,'model_goods'), 'table_view_goods')
        self.create_table_view(getattr(self,'model_purchase'), 'table_view_purchase')
        self.create_table_view(getattr(self,'model_orders'), 'table_view_orders')

        self.table_view_stat = QtWidgets.QTableView()
        self.table_view_stat.setObjectName('table_view_stat')
        self.table_view_stat.horizontalHeader().setSectionResizeMode(1)

        self.table_view_debug = QtWidgets.QTableView()
        self.table_view_debug.setObjectName('table_view_debug')
        self.table_view_debug.horizontalHeader().setSectionResizeMode(1)

        # при нажатии на ячейку срабатывает ивентлуп
        self.table_view_goods.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_goods.selectionModel().selectionChanged.connect(self.items_selected)
        self.table_view_goods.horizontalHeader().setProperty('goods', True)

        self.table_view_purchase.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_purchase.selectionModel().selectionChanged.connect(self.items_selected)
        self.table_view_purchase.horizontalHeader().setProperty('purchases', True)

        self.table_view_orders.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_orders.selectionModel().selectionChanged.connect(self.items_selected)
        self.table_view_orders.horizontalHeader().setProperty('orders', True)

    def widgets_setup(self):
        # ____________________________________ TAB WIDGET SETUP _________________________
        self.tab_widget = QtWidgets.QTabWidget()
        tab_widgets_list = [self.table_view_goods, self.table_view_purchase, self.table_view_orders,
                            self.table_view_stat, self.table_view_debug]
        for widg in tab_widgets_list:
            self.tab_widget.addTab(widg, widg.objectName()[11:].capitalize())
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # _____________________________________ ADD WIDGET SETUP _______________________________
        self.window_add_many_purchases = AddWidget()
        self.window_add_many_purchases.add_button.clicked.connect(self.action_add_many_purchases)

        # _______________________________________BUTTONS_LAYER__________________________________
        self.lnedit_finder = QtWidgets.QLineEdit()
        self.lnedit_finder.setPlaceholderText('Пошук')
        self.lnedit_finder.setCompleter(goods_completer)
        self.lnedit_finder.returnPressed.connect(self.lnedit_finder_pressed)
        self.lnedit_finder.setMaximumWidth(500)

        self.btn_new_goods = QtWidgets.QPushButton()
        self.btn_new_goods.setIcon(QtGui.QIcon(f'{BASEDIR}/static/icons/postal.png'))
        self.btn_new_goods.setObjectName('new_goods')
        self.btn_new_goods.setText('Додати Товар')
        self.btn_new_goods.clicked.connect(self.btn_new_goods_clicked)

        self.btn_new_purchase = QtWidgets.QPushButton()
        self.btn_new_purchase.setIcon(QtGui.QIcon(f'{BASEDIR}/static/icons/purchasing.png'))
        self.btn_new_purchase.setObjectName('new_purchase')
        self.btn_new_purchase.setText('Додати Закупку')
        self.btn_new_purchase.clicked.connect(self.btn_add_purchase_clicked)

        self.btn_new_order = QtWidgets.QPushButton()
        self.btn_new_order.setIcon(QtGui.QIcon(f'{BASEDIR}/static/icons/selling.png'))
        self.btn_new_order.setObjectName('new_order')
        self.btn_new_order.setText('Додати продажу')
        self.btn_new_order.clicked.connect(self.btn_add_order_clicked)

        self.btn_delete_row = QtWidgets.QPushButton()
        self.btn_delete_row.setIcon(QtGui.QIcon(f'{BASEDIR}/static/icons/trash.png'))
        self.btn_delete_row.setObjectName('delete_row')
        self.btn_delete_row.setText('Видалити')
        self.btn_delete_row.clicked.connect(self.btn_delete_row_clicked)

    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ EDITING LAYER ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.btn_statistics_purchase = QtWidgets.QPushButton()
        self.btn_statistics_purchase.setText('Статистика Закупок')
        self.btn_statistics_purchase.clicked.connect(self.btn_statistics_purchase_clicked)

        self.btn_statistics_order = QtWidgets.QPushButton()
        self.btn_statistics_order.setText('Статистика Продажів')

        self.btn_statistics_order.clicked.connect(self.btn_statistics_order_clicked)

        # __________________________________TEXT_LAYER_________________________
        self.label_info = QtWidgets.QLabel()
        self.label_info.setText('id=???')

        self.date_filter = QtWidgets.QLineEdit()
        self.date_filter.setPlaceholderText('yyyy-mm')
        self.date_filter.setText(INIT_NOW_MONTH)
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
        self.lbl_quick_stat_buy.setProperty('LabelStat', True)
        self.lbl_quick_stat_buy.setObjectName('stat_buy')
        self.lbl_quick_stat_buy.setText('buy_total: \n__ ')

        self.lbl_quick_stat_sell = QtWidgets.QLabel()
        self.lbl_quick_stat_sell.setProperty('LabelStat', True)
        self.lbl_quick_stat_sell.setObjectName('stat_sell')
        self.lbl_quick_stat_sell.setText('sell_total: \n__ ')

        # ____________________________________ MODELS _________________________________
        self.model_purchase.setRelation(1, sql_pyqt.QSqlRelation("goods", 'id', 'name'))
        self.model_orders.setRelation(1, sql_pyqt.QSqlRelation("goods", 'id', 'name'))

    def layout_setup(self):
        # ________________________________BUTTONS_LAYOUT___________________________________
        buttons_layout = QtWidgets.QHBoxLayout()

        buttons_layout.addWidget(self.lnedit_finder)
        buttons_layout.addWidget(self.btn_new_goods)
        buttons_layout.addWidget(self.btn_new_purchase)
        buttons_layout.addWidget(self.btn_new_order)
        buttons_layout.addWidget(self.btn_delete_row)

        # ________________________________EDIT WIDGETS_LAYOUT___________________________________
        properties_layout = QtWidgets.QHBoxLayout()

        label_date_layout = QtWidgets.QVBoxLayout()
        label_date_layout.addWidget(self.date_filter)
        label_date_layout.addWidget(self.checkbox_date_filter)
        label_date_layout.addWidget(self.label_info)

        stats_buy_layout = QtWidgets.QVBoxLayout()
        stats_buy_layout.addWidget(self.btn_statistics_purchase, 3)
        stats_buy_layout.addWidget(self.lbl_quick_stat_buy,7)

        stats_sell_layout = QtWidgets.QVBoxLayout()
        stats_sell_layout.addWidget(self.btn_statistics_order, 3)
        stats_sell_layout.addWidget(self.lbl_quick_stat_sell,7)

        properties_layout.addLayout(label_date_layout)
        properties_layout.addSpacing(500)
        properties_layout.addLayout(stats_buy_layout)
        properties_layout.addLayout(stats_sell_layout)

        # ________________________________MAIN_LAYOUT___________________________________________
        top_layout_widget = QtWidgets.QWidget()
        top_layout_widget.setLayout(properties_layout)
        main_layout = QtWidgets.QVBoxLayout()

        splitter = QtWidgets.QSplitter(Qt.Vertical)
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
    def debug_action(self):
        print('DEBUG IS EMPTY')

    def debug_selection_test(self):
        pass

    def items_selected(self):
        table = self.tab_widget.currentWidget()
        selected_rows = table.selectionModel().selectedRows()
        model = table.model()
        rows_ids = (model.index(i.row(), 0).data() for i in selected_rows)
        self.data_cash.selected_rows_ids = rows_ids

    def date_filter_pressed(self):
        self.date_filter_activate()

    def date_filter_activate(self):
        self.update_date_filters()
        self.activate_filter()

    def lnedit_finder_pressed(self):
        self.update_name_filters()
        self.activate_filter()

    def checkbox_filter_clicked(self):
        self.date_filter_activate()

    def btn_new_goods_clicked(self):
        self.action_add_new_goods()
        self.tab_widget.setCurrentIndex(0)
        self.refresh_table(0)

    def btn_add_many_purchases_clicked(self):
        update_goods_completer()
        self.window_add_many_purchases.update_combobox_names()
        self.window_add_many_purchases.refresh_completer()
        self.window_add_many_purchases.show()

    def btn_statistics_purchase_clicked(self):
        self.update_name_filters()
        if self.checkbox_date_filter.isChecked():
            query = self.purchase_query_grouped.get_full_query_grouped('purchase.date', 'name')
        else:
            query = self.purchase_query_grouped.get_full_query_grouped('name')
        self.show_stat_table(query)
        self.calculate_statistic_buy(query)

    def btn_statistics_order_clicked(self):
        self.update_name_filters()
        if self.checkbox_date_filter.isChecked():
            query = self.orders_query_grouped.get_full_query_grouped('orders.date', 'name')
        else:
            query = self.orders_query_grouped.get_full_query_grouped('name')
        self.show_stat_table(query)
        self.calculate_statistic_sell(query)

    def calculate_statistic_buy(self, query_inner):
        query = f'''SELECT SUM(buy_total) FROM ({query_inner[:-1]})'''
        res = dbConnector.general_execution(query)
        self.draw_quick_stat_buy(res[0][0])

    def calculate_statistic_sell(self, query_inner):
        query = f'''SELECT SUM(sell_total) FROM ({query_inner[:-1]})'''
        res = dbConnector.general_execution(query)
        self.draw_quick_stat_sell(res[0][0])

    def tab_changed(self, i):
        self.data_cash.reset_cell_info()
        self.refresh_completer()
        self.activate_filter()
        self.refresh_table(i)
        self.draw_on_label_info()

    def cell_highlighted(self, current):
        self.data_cash.set_cell_info(current, self.tab_widget.currentWidget().model())
        self.draw_on_label_info()

    # ______________________________________ DELETING ___________________________________________
    def btn_delete_row_clicked(self):
        current_table_index = self.tab_widget.currentIndex()

        try:
            rows_ids = list(self.data_cash.selected_rows_ids)
            if current_table_index > 2:
                raise MyExceptions.GeneralException('Видаляти можна тільки в перших трьох таблицях!\n'
                                                    'Це таблиця Статистики!')
            if not rows_ids:
                raise MyExceptions.GeneralException('Спочатку оберіть рядок для видалення(натисніть на номер рядка зліва)')
            self.delete_many_rows(rows_ids, current_table_index)

        except Exception as ex:
            self.draw_error_message('Шось не то =(', exception=ex)

        self.data_cash.reset_cell_info()

    def delete_many_rows(self, rows_ids, table_index):
        if table_index != 0:
            goods_ids_query = f'''SELECT goods_id, COUNT(goods_id)
                                  FROM {TABLE_NAMES_LIST[table_index]} 
                                  WHERE id IN ({", ".join(list(map(str, rows_ids)))})
                                  GROUP BY goods_id'''
            goods_ids = dbConnector.general_execution(goods_ids_query)

            if table_index == 1:
                for row in goods_ids:
                    dbConnector.update_goods_amount(row[0], -row[1])
            elif table_index == 2:
                for row in goods_ids:
                    dbConnector.update_goods_amount(row[0], row[1])

        rows_ids_iter = ((_id,) for _id in rows_ids)
        res = dbConnector.many_execution(f'''DELETE FROM {TABLE_NAMES_LIST[table_index]} WHERE id = ?''', rows_ids_iter)
        if res:
            match res[0]:
                case 'integrity_error':
                    self.draw_error_message('Не можна видаляти, поки є посилання на цей обьєкт в інших таблицях', res)
                case 'general_error':
                    self.draw_error_message('Сталася якась помилка', res)
        self.refresh_table(table_index)

    # __________________________________ SLOTS _____________________________________________
    def activate_filter(self):
        # TODO избавиться от ветвления через if/else
        table_index = self.tab_widget.currentIndex()
        if table_index == 0:
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
            self.model_orders.setFilter(self.orders_query.get_WHERE_filter('name', 'orders.date'))
        else:
            self.model_orders.setFilter(self.orders_query.get_WHERE_filter('name'))

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
        self.orders_query_grouped.set_WHERE_fields({'orders.date': date})

    def refresh_completer(self):
        update_goods_completer()
        self.lnedit_finder.setCompleter(goods_completer)

    def refresh_table(self, table_index):
        if table_index <= 2:
            self.tab_widget.currentWidget().model().select()

    # __________________________________ LOGIC _______________________________________
    # _______________________________ ADD GOODS ________________________________________
    def action_add_new_goods(self):
        dbConnector.insert_into_goods()

    # _________________________________ ADD PURCHASE _____________________________________
    def btn_add_purchase_clicked(self):
        try:
            if self.tab_widget.currentIndex() != 0:
                raise MyExceptions.GeneralException('Додавати потрібно з таблиці "goods"')

            goods_id = self.get_row_id()
            if not goods_id:
                raise MyExceptions.GeneralException('Спочатку оберіть товар який хочете додати з таблиці "goods"')
            self.add_purchase(goods_id)
        except Exception as ex:
            self.draw_error_message('Помилка роботи з таблицею', exception=ex)

    def add_purchase(self, goods_id: int, amount: int = 1, price: int | float = 0, date=INIT_NOW_MONTH):
        purchases_list = [(goods_id, price, date) for _ in range(amount)]
        query = f'''INSERT INTO {dbConnector.TABLE_PURCHASE} VALUES (NULL, ?, ?, ?)'''
        dbConnector.many_execution(query, purchases_list)
        dbConnector.update_goods_amount(goods_id, amount)

        self.tab_widget.setCurrentIndex(1)
        self.refresh_table(1)

    def action_add_many_purchases(self):
        try:
            name, price,amount,date = self.window_add_many_purchases.get_field_data()
            if amount > 1000:
                self.draw_error_message('Можна додавати не більше 1000 штук за раз')
            else:
                goods_id = self.get_goods_id(name)
                if goods_id:
                    self.add_purchase(goods_id,amount,price,date)
        except MyExceptions.InvalidDataField as ex:
            self.draw_error_message('Невірно вказані дані', ex)

    # _________________________________ ADD ORDER _____________________________________
    def btn_add_order_clicked(self):
        try:
            goods_id = self.get_row_id()
            if self.tab_widget.currentIndex() != 0 or not goods_id:
                raise MyExceptions.GeneralException('Додавати потрібно з таблиці "goods"')
            self.add_order(goods_id)
        except Exception as ex:
            self.draw_error_message('Помилка роботи з таблицею', exception=ex)

    def add_order(self, goods_id: int, amount: int = 1, price: int | float = 0, date=INIT_NOW_MONTH):
        for i in range(amount):
            dbConnector.insert_into_orders(goods_id, price, date)
        dbConnector.update_goods_amount(goods_id, -amount)

        self.tab_widget.setCurrentIndex(2)

    def show_stat_table(self, base_query):
        query = sql_pyqt.QSqlQuery(base_query, db=sql_pyqt.db)
        model = sql_pyqt.QSqlQueryModel()
        model.setQuery(query)
        self.table_view_stat.setModel(model)
        self.tab_widget.setCurrentIndex(3)

    def edit_order_cell(self, db_func, value):
        try:
            order_id = int(self.label_info.text().split('=')[1].strip())
            db_func(order_id, value)
            self.refresh_table(2)
        except Exception as ex:
            self.draw_error_message('Спочатку виберіть товар з таблиці "orders"', exception=ex)

    def draw_on_label_info(self):
        row_id = self.get_row_id()
        self.label_info.setText(f'obj_id = {row_id}')

    # __________________________________ FUNCTIONS ____________________________________________
    def get_active_cell_index(self):
        return self.data_cash.get_cell_info('index')

    def get_active_cell_model(self):
        return self.data_cash.get_cell_info('model')

    def get_goods_id(self, goods_name):
        try:
            return dbConnector.select_goods_id(goods_name)[0][0]
        except IndexError as ex:
            self.draw_error_message('Такого товару не знайдено =(', exception=ex)

    def get_row_id(self):
        #todo херово написанный метод. не гибкий!!
        if self.get_active_cell_index():
            try:
                cell_index_row = self.get_active_cell_index().row()
                model = self.get_active_cell_model()
                row_id = model.index(cell_index_row, 0).data()
                return row_id
            except Exception as ex:
                print(ex)

    @staticmethod
    def make_safe_filter_string(text):
        text_safe = re.sub(r'\"+', '', text.strip())
        return text_safe

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
    app.setStyleSheet(style)

    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())
