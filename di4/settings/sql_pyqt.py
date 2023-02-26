from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from di4.settings.config import *
import os

basedir = os.path.dirname(__file__)

db = QSqlDatabase("QSQLITE")
db.setDatabaseName(os.path.join(basedir, DB_NAME))
db.open()







