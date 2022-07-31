from PyQt5 import Qt, QtCore, QtWidgets

from .ui.message_dialog_ui import Ui_Dialog


class MessageDialog(QtWidgets.QDialog):
    def __init__(self, title, message, icon_name, parent):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowIcon(Qt.QIcon(f":/images/images/{icon_name}.ico"))
        self.setWindowTitle(title)

        # Create individual labels for each line of text.
        # Add each label to the scroll area so the text is scrollable.
        message_layout = QtWidgets.QVBoxLayout(self.ui.content)
        for message_line in message.split("\n"):
            line_label = QtWidgets.QLabel(message_line)
            message_layout.addWidget(line_label)

        # TODO: put a frame around the vertical scrollbar

        # Setup UI elements for user interaction.
        self.ui.ok_button.clicked.connect(self.close)

        # Resize the dialog to fit the displayed contents.
        self.adjustSize()
