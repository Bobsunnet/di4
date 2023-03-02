import os
import sqlite3 as sq
from datetime import datetime
from di4.settings.Constants import *

NOW_DATE = datetime.utcnow().date()
directory = os.path.dirname(__file__)

DB_NAME = os.path.join(directory,f'settings/{DB_NAME}')


def general_execution(query):
    with sq.connect(DB_NAME) as connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            return 'Success', None
        except sq.IntegrityError as integrity_error:
            print(f'[ERROR] database problem: {integrity_error}')
            return 'integrity_error', integrity_error
        except Exception as ex:
            print(f'[ERROR] database problem: {ex}')
            return False, ex


def select_execution(query):
    with sq.connect(DB_NAME) as connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            # TODO сделать чтоб метод возвращал просто курсор!!!!!!!!!!!!!
            return cursor.fetchall()
        except sq.IntegrityError as integrity_error:
            print(f'[ERROR] database problem: {integrity_error}')
            return 'integrity_error', integrity_error
        except Exception as ex:
            print(f'[ERROR] database problem: {ex}')
            return False, ex


def insert_into_goods(name='', amount=0):
    insert_query = f'''
            INSERT INTO {TABLE_GOODS} (name, amount)
            VALUES (
            '{name}',
            {amount}); '''
    return general_execution(insert_query)


def insert_into_purchase(goods_id: int, buy_price: int | float = 0, date: datetime = NOW_DATE, status = 1):
    insert_query = f'''
            INSERT INTO {TABLE_PURCHASE} (goods_id, buy_price, date, status)
            VALUES (
            {goods_id},
            {buy_price},
             '{date}',
             {status}); '''
    return general_execution(insert_query)


def insert_into_orders(purchase_id: int, sell_price: int | float = 0, date: datetime = NOW_DATE):
    insert_query = f'''
            INSERT INTO {TABLE_ORDERS} (purchase_id, sell_price, date)
            VALUES (
            {purchase_id},
            {sell_price},
             '{date}'); '''
    return general_execution(insert_query)


def update_goods_amount(id:int, amount:int):
    update_query = f'''
        UPDATE {TABLE_GOODS}
        SET amount = {amount}
        WHERE id = {id};'''
    return general_execution(update_query)


def update_purchase_status(id:int, stat=0):
    update_query = f'''
        UPDATE {TABLE_PURCHASE}
        SET status = {stat}
        WHERE id = {id};'''
    return general_execution(update_query)


def update_order_price(id:int, price:int | float):
    update_query = f'''
        UPDATE {TABLE_ORDERS}
        SET sell_price = {price}
        WHERE id = {id};'''
    return general_execution(update_query)


def update_order_date(id:int, date: str):
    update_query = f'''
        UPDATE {TABLE_ORDERS}
        SET date = '{date}'
        WHERE id = {id};'''
    return general_execution(update_query)


def delete_row(row_id, table):
    del_query = f'''
        DELETE FROM {table}
        WHERE id = '{row_id}';'''
    return general_execution(del_query)


def select_goods_name():
    sel_query = f'''
        SELECT name FROM {TABLE_GOODS};'''
    return select_execution(sel_query)


def select_goods_amount(goods_id):
    sel_query = f'''
        SELECT amount FROM {TABLE_GOODS}
        WHERE id = {goods_id};'''
    return select_execution(sel_query)


def select_goods_id(name):
    sel_query = f'''
        SELECT id FROM {TABLE_GOODS}
        WHERE name = '{name}'
    '''
    return select_execution(sel_query)


create_table_goods = '''
    CREATE TABLE IF NOT EXISTS goods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	amount INTEGER
	);'''

create_table_purchase = '''
    CREATE TABLE IF NOT EXISTS purchase (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    goods_id INTEGER, 
    buy_price REAL,
    date TEXT,
    FOREIGN KEY(goods_id) REFERENCES goods(id))'''

create_table_order = '''
    CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    purchase_id INTEGER, 
    sell_price REAL,
    date TEXT,
    FOREIGN KEY(purchase_id) REFERENCES purchase(id))'''

purchase_summa = ''' SELECT sum(summa)
		FROM (SELECT SUM(buy_price) as summa
        FROM purchase 
        JOIN goods ON purchase.goods_id = goods.id
		WHERE purchase.date LIKE "%2023-03%" 
        GROUP BY goods_id);'''

if __name__ == '__main__':
    print(select_execution(purchase_summa))
    pass