import sqlite3 as sq
from datetime import datetime
from di4.settings.config import *

NOW_DATE = datetime.utcnow().date()


def query_execution(query):
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


def insert_into_goods(name='', amount=0):
    insert_query = f'''
            INSERT INTO {TABLE_GOODS} (name, amount)
            VALUES (
            '{name}',
            {amount}); '''
    return query_execution(insert_query)


def insert_into_purchase(goods_id: int, buy_price: int | float = 0, date: datetime = NOW_DATE):
    insert_query = f'''
            INSERT INTO {TABLE_PURCHASE} (goods_id, buy_price, date)
            VALUES (
            {goods_id},
            {buy_price},
             '{date}'); '''
    return query_execution(insert_query)


def insert_into_orders(purchase_id: int, sell_price: int | float = 0, date: datetime = NOW_DATE):
    insert_query = f'''
            INSERT INTO {TABLE_ORDERS} (purchase_id, sell_price, date)
            VALUES (
            {purchase_id},
            {sell_price},
             '{date}'); '''
    return query_execution(insert_query)


# def select_all_from_refugees():
#     select_all_query = f'''
#     SELECT * FROM {table};
# '''
#     with sq.connect(DATABASE) as connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute(select_all_query)
#         except Exception as ex:
#             print(f'[ERROR] problem: {ex}')
#
#     return cursor.fetchall()
#
#
# def update_city_refugees(id, city):
#     update_query = f'''
#     UPDATE {table}
#     SET city = '{city}'
#     WHERE id = {id};
# '''
#     with sq.connect(DATABASE) as connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute(update_query)
#         except Exception as ex:
#             print(f'[ERROR] problem: {ex}')
#
#
# def update_name_refugees(id, name):
#     update_query = f'''
#     UPDATE {table}
#     SET name = '{name}'
#     WHERE id = {id};
# '''
#     with sq.connect(DATABASE) as connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute(update_query)
#         except Exception as ex:
#             print(f'[ERROR] problem: {ex}')
#
#
# def update_description_refugees(id, description):
#     update_query = f'''
#     UPDATE {table}
#     SET name = '{description}'
#     WHERE id = {id};
# '''
#     with sq.connect(DATABASE) as connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute(update_query)
#         except Exception as ex:
#             print(f'[ERROR] problem: {ex}')
#
#
# def update_contact_id_refugees(id, contact_id):
#     update_query = f'''
#     UPDATE {table}
#     SET name = '{contact_id}'
#     WHERE id = {id};
# '''
#     with sq.connect(DATABASE) as connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute(update_query)
#         except Exception as ex:
#             print(f'[ERROR] problem: {ex}')


def delete_row(row_id):
    del_query = f'''
    DELETE FROM {TABLE_GOODS}
    WHERE id = '{row_id}';
'''
    print(f'dbCOnnecor {row_id}')
    with sq.connect(DB_NAME) as connection:
        try:
            cursor = connection.cursor()
            cursor.execute(del_query)
        except Exception as ex:
            print(f'[ERROR] problem: {ex}')


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

if __name__ == '__main__':
    goods_list = [('bamper_black', 0),
                  ('bamber_red',2),
                  ('spoiler_carbon', 1),
                  ('spoiler_white', 0),
                  ('fara_BNW', 3)]

    purchase_list = [(2,110),
                     (2,113.5),
                     (3,96),
                     (4,125),
                     (5,87.45),
                     (5,89.12),
                     (5,91)]

    orders_list = [(1,140),
                   (3,115.1),
                   (5,123.5)]

    with sq.connect(DB_NAME) as con:
        cursor = con.cursor()
        cursor.executemany(f"INSERT INTO orders VALUES(NULL, ?, ?, '{NOW_DATE}')", orders_list)
