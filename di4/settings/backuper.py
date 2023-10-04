import logging
from datetime import datetime
from di4.settings.Constants import DB_NAME
import shutil
import os

today_date = datetime.now().date()

root_folder = os.path.dirname(__file__)
backup_folder = os.path.join(root_folder, 'backups')

directory_objects = os.listdir(root_folder)


def create_backup_folder():
    if 'backups' not in directory_objects:
        os.mkdir(backup_folder)


def create_db_backup() -> Exception:  # создает новую копию файла и называет с учетом даты создания
    try:
        shutil.copy(os.path.join(root_folder, DB_NAME), backup_folder)
        logging.info('db file was copied')
        try:
            os.rename(os.path.join(backup_folder, DB_NAME), os.path.join(backup_folder, f'{today_date}_{DB_NAME}'))
            logging.info('db backup file was renamed')
        except Exception as ex_rename:
            logging.error(ex_rename)
            return ex_rename
    except Exception as ex_copy:
        logging.error(ex_copy)
        return ex_copy


def create_config_file():
    if 'boot_config.txt' not in directory_objects:
        try:
            with open(os.path.join(root_folder, 'boot_config.txt'), 'w') as conf_file:
                conf_file.write('first run')
                logging.info('config file was created')
        except Exception as ex_create_file:
            logging.error(ex_create_file)


def read_config_file() -> str:
    try:
        with open(os.path.join(root_folder, 'boot_config.txt'), 'r') as conf_file:
            last_update = conf_file.read()
            logging.info('config file was read')
            return last_update
    except Exception as ex_read_file:
        logging.error(ex_read_file)


def write_date_config_file():
    try:
        with open(os.path.join(root_folder, 'boot_config.txt'), 'w') as conf_file:
            conf_file.write(str(today_date))
            logging.info('config date was updated')
    except Exception as ex_write_file:
        logging.error(ex_write_file)


def write_backup():
    # creating config file and folder if doesnt exist
    create_backup_folder()
    create_config_file()
    # reading config data(date) and making backup copy of db file
    config_data = read_config_file()
    if config_data != str(today_date) and config_data is not None:
        record_exception = create_db_backup()
        if not record_exception:
            write_date_config_file()
            logging.info('backup created')


if __name__ == '__main__':
    write_backup()
    print()
    # print(os.listdir(os.getcwd()))
