import io

from PyQt5 import QtCore, Qt, QtWidgets

from libhpl import convert_from_hpl, set_index_color

from .ui.palettedialog_ui import Ui_Dialog

COLOR_BOX_SIZE = 15


class PaletteDialog(QtWidgets.QDialog):

    palette_data_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        QtWidgets.QDialog.__init__(self, parent, flags=flags)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Palette Data")

        self.palette_data = io.BytesIO()
        self.palette_x = 0
        self.palette_y = 0

        # Set up our palette viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.palette_scene = QtWidgets.QGraphicsScene()
        self.ui.png_view.setScene(self.palette_scene)

        self.ui.png_view.mouseDoubleClickEvent = self.mouse_double_click_event
        self.ui.png_view.mousePressEvent = self.mouse_click_event

    def get_palette_img(self):
        """
        Get the palette image for conversion to an HPL file.
        """
        return self.palette_data

    def _set_palette_index_color(self):
        """
        Pick a color and set it as the color for the current palette index.
        If we successfully choose a color we modify the palette data and update the palette view,
        as well as the sprite preview in the main window.
        If the color dialog is cancelled no color data is modified.
        """
        dialog = QtWidgets.QColorDialog()
        accepted = dialog.exec_()

        if accepted:
            qcolor = dialog.currentColor()
            color_tuple = (qcolor.red(), qcolor.green(), qcolor.blue())
            palette_index = (self.palette_x, self.palette_y)

            try:
                set_index_color(self.palette_data, palette_index, color_tuple)

            except Exception:
                message = f"Failed to change the color for palette index ({self.palette_x}, {self.palette_y})!"
                self.parent().show_error_dialog("Error Updating Palette", message)
                return

            self._update_png_view()
            self.palette_data_changed.emit()

    def mouse_double_click_event(self, _):
        """
        Event handler for double clicks on the palette view.
        Picks the color for the current palette index.
        """
        # The palette index will be set via `mouse_click_event` before getting here.
        self._set_palette_index_color()

    def mouse_click_event(self, evt):
        """
        Event handler for single button press on the palette view.
        Sets the palette index for `mouse_double_click_event` so the color picker can
        set the color for the correct index.
        """
        x = evt.x()
        y = evt.y()

        # Convert the mouse event coordinates into an (x, y) palette index
        # This is the (x, y) coordinate of our 256 color palette.
        self.palette_x = x // COLOR_BOX_SIZE
        self.palette_y = y // COLOR_BOX_SIZE

    def set_palette_index(self, palette_index):
        """
        Set the current palette index manually and choose a color for it.
        Used by the main window when the sprite view is double-clicked.
        """
        self.palette_x = palette_index[0]
        self.palette_y = palette_index[1]
        self._set_palette_index_color()

    def _update_png_view(self):
        """
        Refresh the palette view so it is up to date with recent changes.
        """
        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(self.palette_data.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.palette_scene.clear()
        self.palette_scene.addPixmap(png_pixmap)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.png_view.viewport().update()

    def set_palette(self, palette_path):
        """
        Load a palette from file and display the data in the dialog.
        """
        self.palette_data = io.BytesIO()
        convert_from_hpl(palette_path, COLOR_BOX_SIZE, self.palette_data)
        self._update_png_view()
