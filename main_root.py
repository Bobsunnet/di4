from di4.main import *

STYLES_PATH = f'{BASEDIR}/static/style/style.css'

with open(STYLES_PATH, 'r') as file:
    style = file.read()


if __name__ == '__main__':
    write_backup()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(style)

    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())

