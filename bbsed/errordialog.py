import traceback

from PyQt5 import Qt, QtCore, QtWidgets

from .ui.errordialog_ui import Ui_Dialog


def format_exc(exc_info):
    """
    Format exception info. This is expected to be the tuple returned by sys.exc_info().
    """
    return "".join(traceback.format_exception(*exc_info)).strip()


class ErrorDialog(QtWidgets.QDialog):
    def __init__(self, title, message, exc_info, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowIcon(Qt.QIcon(":/images/images/error.ico"))
        self.setWindowTitle(title)

        self.ui.message.setText(message)
        self.ui.traceback.setText(format_exc(exc_info))
        self.ui.traceback.hide()

        # Setup UI elements for user interaction.
        self.ui.toggle_tb.clicked.connect(self.toggle_tb)
        self.ui.ok_button.clicked.connect(self.close)

        # Resize the dialog to fit the displayed contents.
        self.adjustSize()

    def toggle_tb(self):
        """
        Our toggle button has been clicked.
        If the traceback is shown, hide it. If the traceback is hidden, show it.
        We need to resize the dialog after this operation so we do not have blank space
        or inadvertently create a scroll area.
        """
        new_state = not self.ui.traceback.isHidden()
        self.ui.traceback.setHidden(new_state)
        self.adjustSize()
