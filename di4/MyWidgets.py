from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets

from di4.settings import MyExceptions
from di4.settings.Constants import VALIDATOR_DIGITS, NOW_DATE

INIT_NOW_DAY = NOW_DATE.strftime('%Y-%m-%d')


class MyTableView(QtWidgets.QTableView):
    """ Добавляет """
    def __init__(self, mainWindow):
        super(MyTableView, self).__init__()
        self.parent_window = mainWindow # the mainWindow instance
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu)

    def right_menu(self, pos):
        menu = QtWidgets.QMenu()

        # Add menu options
        add_purchase_option = menu.addAction('Add Purchase(in testing...)')
        add_order_option = menu.addAction('Add Order(in testing...)')

        # Menu option events
        add_purchase_option.triggered.connect(self.parent_window.btn_add_purchase_clicked)
        add_order_option.triggered.connect(self.parent_window.btn_add_order_clicked)

        # Position
        menu.exec_(self.mapToGlobal(pos))


class AddWidget(QtWidgets.QWidget):
    def __init__(self, update_names_func, goods_completer, goods_names):
        super().__init__()
        update_names_func() # link to "update_goods_names"
        self.goods_completer = goods_completer
        self.goods_names = goods_names

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
        self.update_combobox_names(self.goods_names)
        self.refresh_completer()

    def refresh_completer(self):
        self.combox_goods_names.setCompleter(self.goods_completer)

    def get_field_data(self):
        """ Возвращает данные с полей окна "Add_many_Purchase"
        :return: goods_name, price, amount, date """
        goods_name = self.combox_goods_names.currentText()
        date = self.field_date.text()
        amount_field = self.field_amount.text()
        if not amount_field:
            raise MyExceptions.InvalidDataField('Невірно заповнене поле')
        amount = int(amount_field)
        price = float(self.field_price.text()) if self.field_price.text() else 0
        return goods_name, price, amount, date

    def update_combobox_names(self, goods_names):
        self.goods_names = goods_names
        self.combox_goods_names.clear()
        self.combox_goods_names.addItems(self.goods_names)


def main():
    pass   


if __name__ == '__main__': 
    main()
