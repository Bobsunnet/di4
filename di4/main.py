import os
import re
import sys
import logging

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QModelIndex

from di4 import dbConnector
from di4.settings import sql_pyqt
from di4.settings import Constants as const
from di4.settings import MyExceptions
from di4.settings.querymaker import QueryMaker, QueryMakerGroupBy, QueryMakerTemplate
from di4.settings.backuper import write_backup

from di4.MyWidgets import AddPurchaseWidget
from di4.MainGuiMixin import MainGuiMixin
from di4.Utils import CurrentDataOperator
from di4.GoodsNamesListUpdater import GoodsNamesList

file_log = logging.FileHandler('logfile.log')
console_log = logging.StreamHandler()

logging.basicConfig(handlers=(file_log, console_log),
                    encoding='UTF-8',
                    level=logging.ERROR,
                    format='[%(levelname)s] ** %(asctime)s ** |%(filename)s|:{%(funcName)s} ** "%(message)s"',
                    datefmt='%Y-%m-%d %H:%M:%S')

BASEDIR = os.path.dirname(__file__)
ICONS_DIR = f'{BASEDIR}/static/icons/'
STYLES_PATH = os.path.join(BASEDIR, 'static/style/style.css')

with open(STYLES_PATH, 'r') as file:
    style = file.read()

TABLE_NAMES_LIST = [dbConnector.TABLE_GOODS, dbConnector.TABLE_PURCHASE, dbConnector.TABLE_ORDERS]


class MainWindow(MainGuiMixin, QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_query_makers()
        self.data_cash = CurrentDataOperator()

        self.model_init(dbConnector.TABLE_GOODS, const.HEADERS_GOODS, 'model_goods')
        self.model_init(dbConnector.TABLE_PURCHASE, const.HEADERS_PURCHASE, 'model_purchase')
        self.model_init(dbConnector.TABLE_ORDERS, const.HEADERS_ORDERS, 'model_orders')
        # todo срабатывает дважды из-за сигнала dataChanged и model editStrategy OnFieldChanged
        self.data_cash.models_list[const.MODEL_GOODS].dataChanged.connect(GoodsNamesList().update_goods_names_list)

        self.table_view_setup_logic()
        self.widgets_setup_ui()
        self.widgets_setup_connections()
        self.layout_setup()
        self.tool_bar_setup()

        self.set_active_model()

    def tool_bar_setup(self):
        tool_bar = QtWidgets.QToolBar('Main toolbar')
        tool_bar.setIconSize(QtCore.QSize(24, 24))
        self.addToolBar(tool_bar)

        self.act_debug = QtWidgets.QAction(QtGui.QIcon(f'{ICONS_DIR}bug.png'), 'debug', self)
        self.act_debug.triggered.connect(self.debug_action)
        self.act_add_many_purchases = QtWidgets.QAction('Кілька закупок')
        font = self.act_add_many_purchases.font()
        font.setPixelSize(24)
        self.act_add_many_purchases.setFont(font)
        # todo сделать отдельным потоком это действие
        self.act_add_many_purchases.triggered.connect(self.btn_add_many_purchases_clicked)

        tool_bar.addAction(self.act_debug)
        tool_bar.addSeparator()
        tool_bar.addAction(self.act_add_many_purchases)

    def model_init(self, table: str, headers: list, model_name: str):
        """ Создает модель QSqlRelationalTableModel и добавляет в список моделей """
        model = sql_pyqt.QSqlRelationalTableModel(db=sql_pyqt.db)
        model.setTable(table)  # привязывает таблицу БД по названию
        model.setEditStrategy(sql_pyqt.QSqlTableModel.EditStrategy.OnFieldChange)
        model.sort(0, Qt.SortOrder.DescendingOrder)
        for i, name in enumerate(headers):
            model.setHeaderData(i + 1, Qt.Orientation.Horizontal, name)

        model.select()
        self.data_cash.models_list.append(model)

    def init_query_makers(self):
        self.relationModel_query_maker = QueryMaker('table_name')
        self.purchase_query_grouped = QueryMakerGroupBy('purchase', 'goods.name', const.BASE_TOTAL_PURCHASES)
        self.orders_query_grouped = QueryMakerGroupBy('orders', 'goods.name', const.BASE_TOTAL_ORDERS)
        self.profit_stat_query = QueryMakerTemplate(const.AVG_PROFIT_STAT_TEMPLATE)

        self.query_makers = [
            self.relationModel_query_maker,
            self.purchase_query_grouped,
            self.orders_query_grouped,
            self.profit_stat_query
        ]

        for q_maker in self.query_makers:
            q_maker.set_date_between_filter(const.INIT_TWO_MONTH_AGO, const.INIT_NOW_MONTH)
            q_maker.set_name_like_filter('')

    def widgets_setup_connections(self):
        # ____________________________________ TAB WIDGET SETUP _________________________
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # _____________________________________ ADD PURCHASE WIDGET SETUP _______________________________
        self.window_add_many_purchases = AddPurchaseWidget()
        self.window_add_many_purchases.add_button.clicked.connect(self.action_add_many_purchases)

        # _______________________________________BUTTONS_LAYER__________________________________
        self.refresh_completer()
        self.lnedit_finder.returnPressed.connect(self.lnedit_finder_pressed)

        self.btn_new_goods.setIcon(QtGui.QIcon(ICONS_DIR + 'postal.png'))
        self.btn_new_goods.clicked.connect(self.btn_new_goods_clicked)

        self.btn_new_purchase.setIcon(QtGui.QIcon(ICONS_DIR + 'purchasing.png'))
        self.btn_new_purchase.clicked.connect(self.btn_add_purchase_clicked)

        self.btn_new_order.setIcon(QtGui.QIcon(ICONS_DIR + 'selling.png'))
        self.btn_new_order.clicked.connect(self.btn_add_order_clicked)

        self.btn_delete_row.setIcon(QtGui.QIcon(ICONS_DIR + 'trash.png'))
        self.btn_delete_row.clicked.connect(self.btn_delete_row_clicked)

        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ EDITING LAYER ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.btn_statistics_purchase.clicked.connect(self.btn_statistics_purchase_clicked)
        self.btn_statistics_order.clicked.connect(self.btn_statistics_order_clicked)
        self.btn_statistics_profit.clicked.connect(self.btn_statistics_profit_clicked)

        # __________________________________TEXT_LAYER_________________________
        self.lnedit_date_start_filter.returnPressed.connect(self.date_filter_pressed)
        self.lnedit_date_end_filter.returnPressed.connect(self.date_filter_pressed)

        self.checkbox_date_filter.setChecked(True)
        ch_box = self.checkbox_date_filter
        ch_box.clicked.connect(lambda: ch_box.setText('On') if ch_box.isChecked() else ch_box.setText('Off'))
        ch_box.clicked.connect(
            lambda: self.set_lnedit_date_filters_enable(
                True) if ch_box.isChecked() else self.set_lnedit_date_filters_enable(False))
        ch_box.clicked.connect(self.checkbox_filter_clicked)

        # ____________________________________ MODELS _________________________________
        self.get_model(const.MODEL_PURCHASE).setRelation(1, sql_pyqt.QSqlRelation("goods", 'id', 'name'))
        self.get_model(const.MODEL_ORDERS).setRelation(1, sql_pyqt.QSqlRelation("goods", 'id', 'name'))


    # _____________________________________ SIGNALS/ACTIONS ___________________________________________
    def set_lnedit_date_filters_enable(self, isEnable):
        self.lnedit_date_start_filter.setEnabled(isEnable)
        self.lnedit_date_end_filter.setEnabled(isEnable)

    def debug_action(self):
        print('Debug info')

    def get_model(self, model_num:int)-> sql_pyqt.QSqlTableModel | sql_pyqt.QSqlRelationalTableModel:
        return self.data_cash.models_list[model_num]

    def col_header_double_clicked(self, col: int):
        """Сортирует по двойному клику на колонке"""
        model = self.data_cash.get_active_model()
        self.sort_table_column(model, col)

    def sort_table_column(self, model, col: int):
        if self.data_cash.current_column.sorted_asc:
            model.sort(col, Qt.DescendingOrder)
        else:
            model.sort(col, Qt.AscendingOrder)

        self.data_cash.current_column.change_header_name(model, col)  # меняет имя хедера
        self.data_cash.current_column.change_sorted_status(model, col)  # меняет статус отсортированности

    def set_active_model(self):
        active_model = self.tab_widget.currentWidget().model()
        self.data_cash.set_active_model(active_model)

    def date_filter_pressed(self):
        self.date_filter_activate()

    def date_filter_activate(self):
        self.update_query_filters()
        self.activate_filter()

    def lnedit_finder_pressed(self):
        self.update_query_filters()
        self.activate_filter()

    def checkbox_filter_clicked(self):
        self.date_filter_activate()

    def btn_new_goods_clicked(self):
        self.action_add_new_goods()
        self.tab_widget.setCurrentIndex(0)
        self.refresh_table(0)

    def __update_goods_names_list(self):
        GoodsNamesList().update_goods_names_list()

    def btn_add_many_purchases_clicked(self):
        """ Открывает окно добавление нескольких закупок """
        # update_goods_completer()
        self.__update_goods_names_list()
        self.window_add_many_purchases.update_combobox()
        self.window_add_many_purchases.show()

    def btn_statistics_purchase_clicked(self):
        """ Рассчитывает и отображает таблицу статистики по закупкам """
        self.update_query_filters()
        if self.checkbox_date_filter.isChecked():
            query = self.purchase_query_grouped.get_full_query_grouped('date', 'name')
        else:
            query = self.purchase_query_grouped.get_full_query_grouped('name')
        self.show_stat_table(query)
        self.calculate_statistic_buy(query)
        self.rename_tab(3, 'Purchases stat')

    def btn_statistics_order_clicked(self):
        self.update_query_filters()
        if self.checkbox_date_filter.isChecked():
            query = self.orders_query_grouped.get_full_query_grouped('date', 'name')
        else:
            query = self.orders_query_grouped.get_full_query_grouped('name')
        self.show_stat_table(query)
        self.calculate_statistic_sell(query)
        self.rename_tab(3, 'Sells stat')

    def btn_statistics_profit_clicked(self):
        self.update_query_filters()
        if self.checkbox_date_filter.isChecked():
            query = self.profit_stat_query.get_full_query('date', 'name')
        else:
            query = self.profit_stat_query.get_full_query('name')
        self.show_stat_table(query)
        self.calculate_statistic_profit(query)
        self.rename_tab(3, 'Profit stat')

    def calculate_statistic_buy(self, query_inner):
        query = f'''SELECT SUM(buy_total) FROM ({query_inner})'''
        res = dbConnector.general_execution(query)
        self.draw_quick_stat_buy(res[0][0])

    def calculate_statistic_sell(self, query_inner):
        query = f'''SELECT SUM(sell_total) FROM ({query_inner})'''
        res = dbConnector.general_execution(query)
        self.draw_quick_stat_sell(res[0][0])

    def calculate_statistic_profit(self, query_inner):
        query = f'''SELECT ROUND(SUM(total_profit), 2) FROM ({query_inner})'''
        res = dbConnector.general_execution(query)
        self.draw_quick_stat_profit(res[0][0])

    def tab_changed(self, i):
        self.__update_goods_names_list()
        self.data_cash.reset_cell_info()
        self.refresh_completer()
        self.activate_filter()
        self.set_active_model()
        self.refresh_table(i)
        self.draw_id_info()

    def cell_highlighted(self, current):
        """ Срабатывает когда выделяется ячейка таблицы
        current - выделенная ячейка """
        self.data_cash.set_index(current)
        self.data_cash.set_model(self.tab_widget.currentWidget().model())
        self.draw_id_info()

    # ______________________________________ DELETING ___________________________________________
    def btn_delete_row_clicked(self):
        try:
            if self.tab_widget.currentIndex() > 2:
                raise MyExceptions.GeneralException('Видаляти можна тільки в перших трьох таблицях!\n'
                                                    'Це таблиця Статистики!')
            self.delete_many_rows()

        except Exception as ex:
            self.draw_error_message('Шось не то =(', exception=ex)
            logging.error(ex)

        self.data_cash.reset_cell_info()

    def delete_many_rows(self):
        is_orders_model: bool = self.tab_widget.currentIndex() == const.MODEL_ORDERS
        table_view: QtWidgets.QTableView = self.tab_widget.currentWidget()
        indexes = table_view.selectionModel().selectedRows()
        rows = [index.row() for index in indexes]
        if not rows:
            raise MyExceptions.GeneralException('Спочатку оберіть рядок для видалення(натисніть на номер рядка зліва)')

        self.delete_rows(table_view.model(), rows, is_orders_model)
        self.refresh_table(self.tab_widget.currentIndex())

    def delete_rows(self, model: sql_pyqt.QSqlTableModel | sql_pyqt.QSqlRelationalTableModel, rows: list,
                    is_orders_model: bool = False):
        if not is_orders_model:
            for row in rows:
                model.removeRow(row)

        else:
            for row in rows:
                name = model.record(row).value(1)
                self.update_goods_amount(name, 1)
                model.removeRow(row)

        model.submitAll()
        model.select()

    # __________________________________ SLOTS _____________________________________________
    def rename_tab(self, index: int, name: str):
        self.tab_widget.setTabText(index, name)

    def get_active_tab_index(self):
        return self.tab_widget.currentIndex()

    def activate_filter(self):
        # TODO избавиться от ветвления через if/else
        table_index = self.get_active_tab_index()
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

    def draw_quick_stat_profit(self, text):
        self.lbl_quick_stat_profit.setText(f'total_avg_profit: \n{text}')

    def activate_filter_goods(self):
        self.get_model(const.MODEL_GOODS).setFilter(self.relationModel_query_maker.get_sqlRelationModel_filter('name'))

    def activate_filter_purchase(self):
        if self.checkbox_date_filter.isChecked():
            self.get_model(const.MODEL_PURCHASE).setFilter(self.relationModel_query_maker.get_sqlRelationModel_filter('name', 'date'))
        else:
            self.get_model(const.MODEL_PURCHASE).setFilter(self.relationModel_query_maker.get_sqlRelationModel_filter('name'))

    def activate_filter_orders(self):
        if self.checkbox_date_filter.isChecked():
            self.get_model(const.MODEL_ORDERS).setFilter(self.relationModel_query_maker.get_sqlRelationModel_filter('name', 'date'))
        else:
            self.get_model(const.MODEL_ORDERS).setFilter(self.relationModel_query_maker.get_sqlRelationModel_filter('name'))

    def update_name_filters(self):
        name = self.make_safe_filter_string(self.lnedit_finder.text())
        for q_maker in self.query_makers:
            q_maker.set_name_like_filter(name)

    def update_query_filters(self):
        date_start = self.make_safe_filter_string(self.lnedit_date_start_filter.text())
        date_end = self.make_safe_filter_string(self.lnedit_date_end_filter.text())
        name = self.make_safe_filter_string(self.lnedit_finder.text())
        for q_maker in self.query_makers:
            q_maker.set_name_like_filter(name)
            q_maker.set_date_between_filter(date_start, date_end)

    def refresh_completer(self):
        self.lnedit_finder.setCompleter(GoodsNamesList().create_completer())

    def refresh_table(self, table_index):
        if table_index <= 2:
            self.tab_widget.currentWidget().model().select()

    # __________________________________ LOGIC _______________________________________
    # _______________________________ ADD GOODS ________________________________________
    def action_add_new_goods(self):
        model: sql_pyqt.QSqlTableModel = self.data_cash.models_list[const.MODEL_GOODS]
        row = model.rowCount()
        model.insertRow(row)
        model.setData(model.index(row, 1), '')
        model.setData(model.index(row, 2), 0)
        model.submitAll()

    # _________________________________ DB OPERATIONS ______________________________
    def insert_operation(self,
                         model: sql_pyqt.QSqlRelationalTableModel,
                         goods_id: int,
                         amount: int = 1,
                         price: int | float = 0,
                         date=const.INIT_NOW_DAY):
        for i in range(amount):
            row = model.rowCount()
            model.insertRow(row)
            model.setData(model.index(row, 1), goods_id)
            model.setData(model.index(row, 2), price)
            model.setData(model.index(row, 3), date)
            model.submitAll()

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
            logging.error(ex)

    def add_purchase(self, goods_id: int, amount: int = 1, price: int | float = 0, date=const.INIT_NOW_DAY):
        model = self.data_cash.models_list[const.MODEL_PURCHASE]
        self.insert_operation(model, goods_id, amount, price, date)
        self.tab_widget.setCurrentIndex(const.MODEL_PURCHASE)
        self.refresh_table(const.MODEL_PURCHASE)

    def action_add_many_purchases(self):
        """Добавляет несколько записей в таблицу покупок"""
        try:
            name, price, amount, date = self.window_add_many_purchases.get_input_fields_data()
            if amount > 100:
                self.draw_error_message('Можна додавати не більше 100 штук за раз')
            else:
                goods_id = self.get_goods_id(name)
                if goods_id:
                    self.add_purchase(goods_id, amount, price, date)
        except MyExceptions.InvalidDataField as ex:
            self.draw_error_message('Невірно вказані дані', ex)
            logging.error(ex)

    # _________________________________ ADD ORDER _____________________________________
    def btn_add_order_clicked(self):
        try:
            goods_id = self.get_row_id()
            if self.tab_widget.currentIndex() != 0 or not goods_id:
                raise MyExceptions.GeneralException('Додавати потрібно з таблиці "goods"')
            self.add_orders(goods_id)
        except Exception as ex:
            self.draw_error_message('Помилка роботи з таблицею', exception=ex)
            logging.error(ex)

    def add_orders(self, goods_id: int, amount: int = 1, price: int | float = 0, date=const.INIT_NOW_DAY):
        model = self.data_cash.models_list[const.MODEL_ORDERS]
        self.insert_operation(model, goods_id, amount, price, date)
        self.update_goods_amount(goods_id, -amount)
        self.tab_widget.setCurrentIndex(const.MODEL_ORDERS)

    def update_goods_amount(self, goods_name_id: int | str, amount: int):
        model: sql_pyqt.QSqlRelationalTableModel = self.data_cash.models_list[const.MODEL_GOODS]

        search_col = 0 if isinstance(goods_name_id, int) else 1

        goods_index: list[QModelIndex] = model.match(model.index(0, search_col),
                                                                      Qt.DisplayRole,
                                                                      goods_name_id,
                                                                      hits=1,
                                                                      flags=Qt.MatchExactly)
        if not goods_index:
            raise MyExceptions.InvalidDataField("Невірний id товару")

        row: int = goods_index[0].row()
        amount = model.data(model.index(row, 2)) + amount
        model.setData(model.index(row, 2), amount)
        model.submitAll()

    def show_stat_table(self, base_query):
        """ Создает модель на основе SQL запроса и отображает ее в таблице"""
        query = sql_pyqt.QSqlQuery(base_query, db=sql_pyqt.db)
        model = sql_pyqt.QSqlQueryModel()
        model.setQuery(query)
        proxy_model = QSortFilterProxyModel()  # прокси модель нужна для сортировки
        proxy_model.setSourceModel(model)

        self.table_view_stat.setModel(proxy_model)
        self.tab_widget.setCurrentIndex(3)
        self.set_active_model()

    def draw_id_info(self):
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
            logging.error(ex)

    def get_row_id(self):
        # todo херово написанный метод. не гибкий!!
        """ Возвращает индекс поля БД выделенной ячейки таблицы"""
        if self.get_active_cell_index():
            try:
                cell_index_row = self.get_active_cell_index().row()
                model = self.get_active_cell_model()
                row_id = model.index(cell_index_row, 0).data()
                return row_id

            except Exception as ex:
                logging.error(ex)
                print(ex)

    @staticmethod
    def make_safe_filter_string(text):
        """Переделывает строку для избежания SQL-инъекций"""
        text_safe = re.sub(r'\";+', '', text.strip())
        return text_safe

    def draw_error_message(self, error_text, exception: Exception = 'Undefined'):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Щось пішло не так =(')
        msg.setText(error_text)
        msg.setInformativeText(f'{exception}')

        msg.exec_()


if __name__ == '__main__':
    write_backup()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(style)

    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())
