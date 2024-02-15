from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlRelationalTableModel, QSqlRelation, QSqlQueryModel, QSqlQuery
from di4.settings.Constants import *
import os

basedir = os.path.dirname(__file__)

db = QSqlDatabase("QSQLITE")
db.setDatabaseName(os.path.join(basedir, DB_NAME))
db.open()




if __name__ == '__main__':
    model = QItemSelectionModel().changed


