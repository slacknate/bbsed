import sys

from PyQt5 import QtCore, QtWidgets


class WorkThreadError(Exception):
    """
    An exception to pass along a standard error to the user.
    Used to fast-fail for an error scenario that does not require viewing a traceback.
    """
    def __init__(self, title, message):
        self.message = message
        self.title = title

    def get_details(self):
        """
        Return a tuple of error details we can pass to `MainWindow.show_message_dialog()`.
        """
        return self.title, self.message, QtWidgets.QMessageBox.Icon.Critical


class WorkThreadException(Exception):
    """
    An exception to pass along information from another exception.
    Used to show a traceback for a fatal error that occurred in a thread.
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
        self.exc = None

    def run(self):
        try:
            self.work()

        except WorkThreadError as error:
            self.error = error

        except WorkThreadException as exc:
            self.exc = exc

        except Exception:
            self.exc = WorkThreadException("Unhandled Error", "Unhandled error occurred!")

    def work(self):
        raise NotImplementedError
