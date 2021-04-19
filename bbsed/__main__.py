from PyQt5 import QtWidgets

from .main_window import MainWindow


def get_app():
    app = QtWidgets.QApplication.instance()

    if app is None:
        app = QtWidgets.QApplication([])

    return app


def main():
    app = get_app()

    window = MainWindow()
    window.init_excepthook()
    window.show()

    app.exec_()


if __name__ == "__main__":
    main()
