import sys

from PyQt5 import QtWidgets


class AppError(Exception):
    """
    Base exception for passing along a standard error to the user.
    Used to fast-fail for an error scenario that does not require viewing a traceback.
    """
    def __init__(self, title, message):
        self.message = message
        self.title = title

    def get_details(self):
        """
        Return a tuple of error details we can pass to `MainWindow.show_message_dialog()`.
        """
        return self.title, self.message, "error"


class AppException(Exception):
    """
    Base exception for passing along information from another exception and display it to the user.
    Used to fast-fail for an error scenario where viewing a traceback would be useful for debugging.
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
