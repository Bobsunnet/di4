from di4.main import *



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    mainWindow = TableWindow()
    mainWindow.show()

    sys.exit(app.exec_())

