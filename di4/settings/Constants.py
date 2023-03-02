from PyQt5 import QtGui, QtCore

DB_NAME = 'bampera.db'
TABLE_GOODS = 'goods'
TABLE_PURCHASE = 'purchase'
TABLE_ORDERS = 'orders'


BASE_QUERY_ORDERS_ALL = '''SELECT orders.id, goods.name, sell_price, orders.date
        FROM orders
        JOIN purchase ON purchase.id = orders.purchase_id
        JOIN goods ON goods.id = purchase.goods_id'''

BASE_TOTAL_PURCHASES = '''SELECT name, SUM(buy_price) as buy_total, COUNT(name) as amount
        FROM purchase JOIN goods ON purchase.goods_id = goods.id'''

BASE_TOTAL_ORDERS = '''SELECT goods.name, SUM(sell_price) as sell_total, COUNT(name) as amount
        FROM orders JOIN purchase ON purchase.id = orders.purchase_id
        JOIN goods ON goods.id = purchase.goods_id'''


VALIDATOR_DIGITS = QtGui.QRegExpValidator(QtCore.QRegExp(r'[0-9.]+'))
