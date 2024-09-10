import logging
import os
import sqlite3 as sq
from di4.settings.Constants import *

DATABASE_ERROR = 'Database error'

directory = os.path.dirname(__file__)
DB_NAME = os.path.join(directory,f'settings/{DB_NAME}')


def many_execution(query, data_arr:list):
    with sq.connect(DB_NAME, timeout=10) as connection:
        try:
            cursor = connection.cursor()
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.executemany(query, data_arr)
            connection.commit()
            return cursor.fetchall()

        except sq.IntegrityError as integrity_error:
            connection.rollback()
            logging.error(f'{DATABASE_ERROR}: {integrity_error}')
            return 'integrity_error', integrity_error

        except Exception as ex:
            connection.rollback()
            logging.error(f'{DATABASE_ERROR}: {ex}')
            return 'general_error', ex


def general_execution(query):
    with sq.connect(DB_NAME, timeout=10) as connection:
        try:
            cursor = connection.cursor()
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.execute(query)
            connection.commit()
            return cursor.fetchall()

        except sq.IntegrityError as integrity_error:
            connection.rollback()
            logging.error(f'{DATABASE_ERROR}: {integrity_error}')
            return 'integrity_error', integrity_error

        except Exception as ex:
            connection.rollback()
            logging.error(f'{DATABASE_ERROR}: {ex}')
            return 'general_error', ex


def insert_into_goods(name='', amount=0):
    insert_query = f'''INSERT INTO {TABLE_GOODS} (name, amount) VALUES ('{name}', {amount});'''
    return general_execution(insert_query)


def update_goods_amount(_id:int, amount:int):
    """ :param amount: if negative - than decrease the amount value """
    update_query = f'''UPDATE {TABLE_GOODS} SET amount = amount + {amount} WHERE id = {_id};'''
    return general_execution(update_query)


def select_goods_name():
    sel_query = f'SELECT name FROM {TABLE_GOODS};'
    return general_execution(sel_query)


def select_goods_amount(goods_id):
    sel_query = f'''
        SELECT amount FROM {TABLE_GOODS}
        WHERE id = {goods_id};'''
    return general_execution(sel_query)


def select_goods_id(name):
    sel_query = f'SELECT id FROM {TABLE_GOODS} WHERE name = "{name}";'
    return general_execution(sel_query)


if __name__ == '__main__':
    get_former_date(30)

