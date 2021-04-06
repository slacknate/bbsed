import io

from PyQt5 import QtCore, Qt, QtWidgets

from .ui.zoomdialog_ui import Ui_Dialog

ZOOM_VIEW_SIZE = 247
ZOOM_VIEW_CENTER = 124
ZOOM_VIEW_SCALE = 5.0


class ZoomDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        QtWidgets.QDialog.__init__(self, parent, flags=flags)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Sprite Zoom")

        self.current_sprite = io.BytesIO()
        self.current_position = Qt.QPoint(0, 0)

        self.zoom_scene = QtWidgets.QGraphicsScene()
        self.ui.png_view.setScene(self.zoom_scene)

        self.ui.png_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.png_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Scale the view so we zoom in.
        self.ui.png_view.scale(ZOOM_VIEW_SCALE, ZOOM_VIEW_SCALE)

    def set_sprite(self, current_sprite):
        """
        Set the sprite that we are zooming in on.
        """
        self.current_sprite = current_sprite

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(self.current_sprite.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.zoom_scene.clear()
        self.zoom_scene.addPixmap(png_pixmap)

        # TODO: draw a crosshair at the center of the zoom view

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
        self.ui.png_view.centerOn(point.x(), point.y())
        self.current_position = point
