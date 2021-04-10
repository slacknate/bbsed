from PyQt5 import QtCore

from .exceptions import AppError, AppException


class WorkThread(QtCore.QThread):
    """
    Base class for work threads.
    Provides basic error handling and a message signal to update the UI.
    """

    message = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.error = None
        self.exc = None

    def run(self):
        try:
            self.work()

        except AppError as error:
            self.error = error

        except AppException as exc:
            self.exc = exc

        except Exception:
            self.exc = AppException("Unhandled Error", "Unhandled error occurred!")

    def work(self):
        raise NotImplementedError
