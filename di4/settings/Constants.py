from PyQt5 import QtGui, QtCore
import datetime

NOW_DATE = datetime.datetime.utcnow().date()


def get_former_date(days):
    """returns date that was some period ago"""
    delta = datetime.timedelta(days)
    former_date = NOW_DATE-delta
    return former_date


DB_NAME = 'bampera.db'
TABLE_GOODS = 'goods'
TABLE_PURCHASE = 'purchase'
TABLE_ORDERS = 'orders'


BASE_QUERY_ORDERS_ALL = '''
            SELECT name,
            sell_price,
            orders.date
            FROM orders
            JOIN goods ON goods.id = orders.goods_id
        '''

BASE_TOTAL_PURCHASES = '''
            SELECT name,
            ROUND(AVG(buy_price), 2) as price_avg,
            SUM(buy_price) as buy_total,
            COUNT(name) as amount
            FROM purchase 
            JOIN goods ON purchase.goods_id = goods.id
        '''

BASE_TOTAL_ORDERS = '''
            SELECT name,
            ROUND(AVG(sell_price), 2) as sell_price_avg,
            SUM(sell_price) as sell_total,
            COUNT(name) as amount
            FROM orders
            JOIN goods ON goods.id = orders.goods_id
        '''

AVG_PROFIT_STAT_TEMPLATE = '''
            SELECT orders_avg.name, 
            price_buy_avg,
            price_sell_avg,
            (price_sell_avg - price_buy_avg) as avg_profit,
            (price_sell_avg - price_buy_avg)*orders_avg.amount as total_profit,
            orders_avg.amount            
            FROM (SELECT name,
                  ROUND(AVG(sell_price), 2) as price_sell_avg,
                  COUNT(name) as amount
                  FROM orders
                  JOIN goods ON orders.goods_id = goods.id
                  {{ WHERE_STATEMENT }}
                  GROUP BY orders.goods_id) orders_avg
            JOIN goods ON goods.name = orders_avg.name
            JOIN (SELECT name,
                  ROUND(AVG(buy_price), 2) as price_buy_avg
                  FROM purchase 
                  JOIN goods ON purchase.goods_id = goods.id
        ''' + f'''
            WHERE date(purchase.date) BETWEEN date('{get_former_date(60).strftime('%Y-%m-%d')}') 
                                      AND date('{NOW_DATE.strftime('%Y-%m-%d')}')
            GROUP BY purchase.goods_id) purchase_avg ON purchase_avg.name = goods.name'''


VALIDATOR_DIGITS = QtGui.QRegExpValidator(QtCore.QRegExp(r'[0-9.]+'))

