from PyQt5 import QtCore, QtWidgets

from .ui.settings_dialog_ui import Ui_Dialog


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, app_config, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("BBCF Sprite Editor Settings")

        self.ui.select_bbcf.clicked.connect(self.select_bbcf_install)
        self.ui.select_steam.clicked.connect(self.select_steam_install)

        self.app_config = app_config

        # Set our previously used install paths if they exist.
        bbcf_install = self.app_config["bbsed"]["bbcf_install"]
        if bbcf_install:
            self.ui.bbcf_install.setText(bbcf_install)

        steam_install = self.app_config["bbsed"]["steam_install"]
        if steam_install:
            self.ui.steam_install.setText(steam_install)

    def select_bbcf_install(self):
        """
        Select the BBCF installation location to be used by the app.
        """
        bbcf_install = QtWidgets.QFileDialog.getExistingDirectory(

            parent=self,
            caption="Select Directory Containing BBCF.exe",
        )

        # If we cancelled the dialog we do not want to save anything.
        if bbcf_install:
            self.ui.bbcf_install.setText(bbcf_install)

    def select_steam_install(self):
        """
        Select the BBCF installation location to be used by the app.
        """
        steam_install = QtWidgets.QFileDialog.getExistingDirectory(

            parent=self,
            caption="Select Directory Containing steam.exe",
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
        bbcf_install = self.ui.bbcf_install.text()

        if steam_install and bbcf_install:
            self.app_config["bbsed"]["steam_install"] = steam_install
            self.app_config["bbsed"]["bbcf_install"] = bbcf_install
            self.app_config.save()
            QtWidgets.QDialog.accept(self)

        else:
            message = "Must select both Steam and BBCF install paths!"
            self.parent().show_message_dialog("Missing Settings", message, "error")
