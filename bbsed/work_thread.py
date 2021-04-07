import sys

from PyQt5 import QtCore


class WorkThreadError(Exception):
    """
    An exception to pass along information from another exception.
    The idea is to allow for exiting a work thread quickly upon fatal error but preserve the original traceback.
    Perhaps `raise from` could fit this need but making the traceback more complicated seems unwise.
    """
    def __init__(self, title, message):
        self.exc_info = sys.exc_info()
        self.message = message
        self.title = title

    def get_details(self):
        """
        Return a tuple of error details we can pass to `MainWindow.show_error_dialog()`.
        """
        return self.title, self.message, self.exc_info


class WorkThread(QtCore.QThread):
    """
    Base class for work threads.
    Provides basic error handling and a message signal to update the UI.
    """

    message = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.error = None

    def run(self):
        try:
            self.work()

        except WorkThreadError as error:
            self.error = error

        except Exception:
            self.error = WorkThreadError("Unhandled Error", "Unhandled error occurred!")

    def work(self):
        raise NotImplementedError
