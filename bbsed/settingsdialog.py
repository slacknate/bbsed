from PyQt5 import QtCore, QtWidgets

from .ui.settingsdialog_ui import Ui_Dialog


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, config, parent=None):
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        QtWidgets.QDialog.__init__(self, parent, flags=flags)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("BBCF Sprite Editor Settings")
        self.ui.select.clicked.connect(self.select_steam_install)

        self.config = config

        # Set our previously used Steam install path if it exists.
        if self.config.steam_install:
            self.ui.steam_install.setText(self.config.steam_install)

    def select_steam_install(self):
        """
        Select the BBCF installation location to be used by the app.
        """
        steam_install = QtWidgets.QFileDialog.getExistingDirectory(

            parent=self,
            caption="Select Steam installation location",
        )

        # If we cancelled the dialog we do not want to save anything.
        if steam_install:
            self.ui.steam_install.setText(steam_install)

    def accept(self):
        """
        When we accept this dialog we check if we have chosen a steam
        installation and if we have we update the config.
        """
        steam_install = self.ui.steam_install.text()

        if steam_install:
            self.config.update(steam_install=steam_install)

        QtWidgets.QDialog.accept(self)