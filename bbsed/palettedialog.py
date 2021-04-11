from PyQt5 import QtCore, Qt, QtWidgets

from .ui.palettedialog_ui import Ui_Dialog

from .util import block_signals

COLOR_BOX_SIZE = 15


class PaletteDialog(QtWidgets.QDialog):

    index_selected = QtCore.pyqtSignal(tuple)

    def __init__(self, menu_check, parent=None):
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        QtWidgets.QDialog.__init__(self, parent, flags=flags)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Palette Data")

        self.menu_check = menu_check
        self.menu_check.triggered.connect(self.setVisible)

        # Set up our palette viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.palette_scene = QtWidgets.QGraphicsScene()
        self.ui.png_view.setScene(self.palette_scene)

        self.ui.png_view.mouseDoubleClickEvent = self.mouse_double_click_event

    def showEvent(self, evt):
        """
        Automatically update the View Menu check state on dialog open.
        """
        QtWidgets.QDialog.showEvent(self, evt)

        # If we do not block signals we will get stuck in an infinite loop.
        with block_signals(self.menu_check):
            self.menu_check.setChecked(True)

    def closeEvent(self, evt):
        """
        Automatically update the View Menu check state on dialog close.
        """
        QtWidgets.QDialog.closeEvent(self, evt)

        # If we do not block signals we will get stuck in an infinite loop.
        with block_signals(self.menu_check):
            self.menu_check.setChecked(False)

    def reset(self):
        """
        Reset the palette view to be blank.
        """
        # Clear our image data.
        self.palette_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.png_view.viewport().update()

    def mouse_double_click_event(self, evt):
        """
        Event handler for double clicks on the palette view.
        We emit a signal to let the sprite editor know we have double clicked on the
        palette dialog and want to pick a color for the given palette index.
        """
        palette_x = evt.x() // COLOR_BOX_SIZE
        palette_y = evt.y() // COLOR_BOX_SIZE

        self.index_selected.emit((palette_x, palette_y))

    def set_palette(self, palette_data):
        """
        Load a palette from file and display the data in the dialog.
        """
        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(palette_data.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.palette_scene.clear()
        self.palette_scene.addPixmap(png_pixmap)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.png_view.viewport().update()
