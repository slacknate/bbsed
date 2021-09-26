import io

from PIL import Image
from PyQt5 import QtCore, Qt, QtWidgets

from .ui.zoom_dialog_ui import Ui_Dialog

from .crosshair import Crosshair
from .util import block_signals

CROSS_HAIR_SIZE = 10
ZOOM_VIEW_SCALE = 2


class ZoomDialog(QtWidgets.QDialog):
    def __init__(self, menu_check, parent=None):
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        QtWidgets.QDialog.__init__(self, parent, flags=flags)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Sprite Zoom")

        self.menu_check = menu_check
        self.menu_check.triggered.connect(self.setVisible)

        self.current_sprite = io.BytesIO()

        self.current_position = Qt.QPoint(0, 0)
        self.crosshair = Crosshair(CROSS_HAIR_SIZE)

        self.zoom_scene = QtWidgets.QGraphicsScene()
        self.ui.png_view.setScene(self.zoom_scene)

        self.ui.png_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.png_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Scale the view so we zoom in.
        self.ui.png_view.scale(ZOOM_VIEW_SCALE, ZOOM_VIEW_SCALE)

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
        Reset the zoom view to be blank.
        """
        # Clear our image data. We have to remove the crosshair item or the C++ object it wraps will
        # be deleted by the scene clear operation.
        self.current_sprite = io.BytesIO()
        self.zoom_scene.removeItem(self.crosshair)
        self.zoom_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.png_view.viewport().update()
        # Reset sprite and zoom information.
        self.current_position = Qt.QPoint(0, 0)

    def set_sprite(self, new_sprite):
        """
        Set the sprite that we are zooming in on.
        """
        self.current_sprite = io.BytesIO()

        # Scale the sprite by our defined zoom factor and set the result as the dialog sprite data.
        with Image.open(new_sprite) as img:
            new_img = img.resize((img.width * ZOOM_VIEW_SCALE, img.height * ZOOM_VIEW_SCALE))
            new_img.save(self.current_sprite, format="PNG")

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(self.current_sprite.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.  We have to remove the crosshair item
        # or the C++ object it wraps will be deleted by the scene clear operation.
        self.zoom_scene.removeItem(self.crosshair)
        self.zoom_scene.clear()

        pixmap_item = self.zoom_scene.addPixmap(png_pixmap)

        # Set the parent item of the crosshair to the added png pixmap so the crosshair can
        # determine what color it should be drawn using the pixmap as a reference.
        # Per Qt-5 documentation, setting the parent item adds the crosshair to the scene of the parent.
        self.crosshair.setParentItem(pixmap_item)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.png_view.viewport().update()

        # Move the cursor. If this is the initial load we move to 0, 0.
        # Otherwise we move the cursor to the last focused position.
        self.move_cursor(self.current_position)

    def move_cursor(self, point):
        """
        Change what part of the sprite we are zoomed in on.
        Maintain a reference to the current center position so if
        we reload the sprite data we can re-center on this position again in `set_sprite`.
        """
        scaled_point = point * ZOOM_VIEW_SCALE

        self.ui.png_view.centerOn(scaled_point)
        self.crosshair.setPos(scaled_point)

        # Ensure the graphics view is refreshed so our crosshair colors update.
        self.ui.png_view.viewport().update()
        self.current_position = point
