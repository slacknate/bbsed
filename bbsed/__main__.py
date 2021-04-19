import ctypes
import platform

from PyQt5 import QtWidgets

from .version import VERSION
from .main_window import MainWindow


def get_app():
    app = QtWidgets.QApplication.instance()

    if app is None:
        app = QtWidgets.QApplication([])

    return app


def set_app_id():
    if platform.system().upper() == "WINDOWS":
        # Group BBCF Sprite Editor instances of the same version together on the taskbar.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"slacknate.bbsed.{VERSION}")


def main():
    set_app_id()
    app = get_app()

    window = MainWindow()
    window.init_excepthook()
    window.show()

    app.exec_()


if __name__ == "__main__":
    main()
