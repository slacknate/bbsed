from PyQt5 import QtCore, QtWidgets

from .ui.about_dialog_ui import Ui_Dialog

from .version import VERSION, REVISION


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("About BBCF Sprite Editor")

        label_contents = f"<b>App Version: </b>{VERSION}<br/>"

        if REVISION is not None:
            label_contents += f"<b>App Revision: </b>{REVISION}<br/>"

        label_contents += f"<br/><b>Qt Version: </b>{QtCore.QT_VERSION_STR}<br/>"
        label_contents += f"<b>PyQt Version: </b>{QtCore.PYQT_VERSION_STR}<br/><br/>"

        self.ui.about.setText(label_contents)
        self.adjustSize()
