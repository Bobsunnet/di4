from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTableView, QHeaderView, QTabWidget, QLineEdit, QPushButton, QLabel, QCheckBox, \
    QHBoxLayout, QVBoxLayout, QWidget, QSplitter

from di4.MyWidgets import MyTableView
from di4.settings import Constants as const


class MainGuiMixin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.table_view_setup_ui()

    def table_view_setup_ui(self):
        self.table_view_stat = QTableView()
        self.table_view_stat.setObjectName('table_view_stat')

        self.table_view_debug = QTableView()
        self.table_view_debug.setObjectName('table_view_debug')

    def create_table_view(self, model, obj_name):
        """ Метод создает table_view обьекты """
        table_view = MyTableView(self) # inserting self(mainWindow instance) as parent_window
        table_view.setObjectName(obj_name)
        table_view.setModel(model)
        table_view.hideColumn(0)
        for i in range(model.columnCount() - 1):
            table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)

        table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        setattr(self, obj_name, table_view)

    def widgets_setup_ui(self):
        # ____________________________________ TAB WIDGET SETUP _________________________
        self.tab_widget = QTabWidget()
        tab_widgets_list = [self.table_view_goods, self.table_view_purchase, self.table_view_orders,
                            self.table_view_stat, self.table_view_debug]
        for widget in tab_widgets_list:
            self.tab_widget.addTab(widget, widget.objectName()[11:].capitalize())

        self.checkbox_date_filter = QCheckBox('On')

        # _______________________________________BUTTONS_LAYER__________________________________
        self.lnedit_finder = QLineEdit()
        self.lnedit_finder.setPlaceholderText('Пошук')
        self.lnedit_finder.setMaximumWidth(500)

        self.btn_new_goods = QPushButton()
        self.btn_new_goods.setObjectName('new_goods')
        self.btn_new_goods.setText('Додати Товар')

        self.btn_new_purchase = QPushButton()
        self.btn_new_purchase.setObjectName('new_purchase')
        self.btn_new_purchase.setText('Додати Закупку')

        self.btn_new_order = QPushButton()
        self.btn_new_order.setObjectName('new_order')
        self.btn_new_order.setText('Додати продажу')

        self.btn_delete_row = QPushButton()
        self.btn_delete_row.setObjectName('delete_row')
        self.btn_delete_row.setText('Видалити')

    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ EDITING LAYER ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.btn_statistics_purchase = QPushButton()
        self.btn_statistics_purchase.setText('Статистика Закупок')

        self.btn_statistics_order = QPushButton()
        self.btn_statistics_order.setText('Статистика Продажів')

        self.btn_statistics_profit = QPushButton()
        self.btn_statistics_profit.setText('Статистика Прибутку')

        # __________________________________TEXT_LAYER_________________________
        self.label_info = QLabel()
        self.label_info.setText('obj_id = None')

        self.lnedit_date_start_filter = QLineEdit()
        self.lnedit_date_start_filter.setPlaceholderText('yyyy-mm')
        self.lnedit_date_start_filter.setText(const.INIT_TWO_MONTH_AGO)
        self.lnedit_date_start_filter.setMaximumWidth(100)

        self.lnedit_date_end_filter = QLineEdit()
        self.lnedit_date_end_filter.setPlaceholderText('yyyy-mm')
        self.lnedit_date_end_filter.setText(const.INIT_NOW_MONTH)
        self.lnedit_date_end_filter.setMaximumWidth(100)

        self.lbl_quick_stat_buy = QLabel()
        self.lbl_quick_stat_buy.setProperty('LabelStat', True)
        self.lbl_quick_stat_buy.setObjectName('stat_buy')
        self.lbl_quick_stat_buy.setText('buy_total: \n__ ')

        self.lbl_quick_stat_sell = QLabel()
        self.lbl_quick_stat_sell.setProperty('LabelStat', True)
        self.lbl_quick_stat_sell.setObjectName('stat_sell')
        self.lbl_quick_stat_sell.setText('sell_total: \n__ ')

        self.lbl_quick_stat_profit = QLabel()
        self.lbl_quick_stat_profit.setProperty('LabelStat', True)
        self.lbl_quick_stat_profit.setObjectName('stat_profit')
        self.lbl_quick_stat_profit.setText('profit_total: \n__ ')

    def layout_setup(self):
        # ________________________________BUTTONS_LAYOUT___________________________________
        buttons_layout = QHBoxLayout()

        buttons_layout.addWidget(self.lnedit_finder)
        buttons_layout.addWidget(self.btn_new_goods)
        buttons_layout.addWidget(self.btn_new_purchase)
        buttons_layout.addWidget(self.btn_new_order)
        buttons_layout.addWidget(self.btn_delete_row)

        # ________________________________EDIT WIDGETS_LAYOUT___________________________________
        properties_layout = QHBoxLayout()

        label_date_layout = QVBoxLayout()
        label_date_layout.addWidget(self.lnedit_date_start_filter)
        label_date_layout.addWidget(self.lnedit_date_end_filter)
        label_date_layout.addWidget(self.checkbox_date_filter)
        label_date_layout.addWidget(self.label_info)

        stats_buy_layout = QVBoxLayout()
        stats_buy_layout.addWidget(self.btn_statistics_purchase, 3)
        stats_buy_layout.addWidget(self.lbl_quick_stat_buy,7)

        stats_sell_layout = QVBoxLayout()
        stats_sell_layout.addWidget(self.btn_statistics_order, 3)
        stats_sell_layout.addWidget(self.lbl_quick_stat_sell,7)

        stats_profit_layout = QVBoxLayout()
        stats_profit_layout.addWidget(self.btn_statistics_profit, 3)
        stats_profit_layout.addWidget(self.lbl_quick_stat_profit, 7)

        properties_layout.addLayout(label_date_layout)
        properties_layout.addSpacing(500)
        properties_layout.addLayout(stats_buy_layout)
        properties_layout.addLayout(stats_sell_layout)
        properties_layout.addLayout(stats_profit_layout)

        # ________________________________MAIN_LAYOUT___________________________________________
        top_layout_widget = QWidget()
        top_layout_widget.setLayout(properties_layout)
        main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(top_layout_widget)
        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([125, 150])

        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(splitter)

        main_layout_widget = QWidget()
        main_layout_widget.setLayout(main_layout)

        self.setCentralWidget(main_layout_widget)

    def table_view_setup_logic(self):
        self.create_table_view(self.get_model(const.MODEL_GOODS), 'table_view_goods')
        self.create_table_view(self.get_model(const.MODEL_PURCHASE), 'table_view_purchase')
        self.create_table_view(self.get_model(const.MODEL_ORDERS), 'table_view_orders')

        self.table_view_stat.horizontalHeader().setSectionResizeMode(1)
        self.table_view_stat.horizontalHeader().sectionDoubleClicked.connect(self.col_header_double_clicked)

        self.table_view_debug.horizontalHeader().setSectionResizeMode(3)
        self.table_view_debug.horizontalHeader().sectionDoubleClicked.connect(self.col_header_double_clicked)

        self.table_view_goods.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_goods.horizontalHeader().setProperty('goods', True)
        self.table_view_goods.horizontalHeader().sectionDoubleClicked.connect(self.col_header_double_clicked)

        self.table_view_purchase.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_purchase.horizontalHeader().setProperty('purchases', True)
        self.table_view_purchase.horizontalHeader().sectionDoubleClicked.connect(self.col_header_double_clicked)

        self.table_view_orders.selectionModel().currentChanged.connect(self.cell_highlighted)
        self.table_view_orders.horizontalHeader().setProperty('orders', True)
        self.table_view_orders.horizontalHeader().sectionDoubleClicked.connect(self.col_header_double_clicked)

    def setup_ui(self):
        self.setWindowTitle('Table Main Window')
        self.setMinimumSize(1000, 600)
