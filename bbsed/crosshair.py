from PyQt5 import Qt, QtWidgets

COLOR_MAX = 255


def inverse_color(qrgba):
    """
    Return the inverse color of the given color.
    We ignore transparency as a crosshair should always be fully opaque.
    """
    color = Qt.QColor.fromRgba(qrgba)
    return Qt.QColor(COLOR_MAX - color.red(), COLOR_MAX - color.green(), COLOR_MAX - color.blue(), COLOR_MAX)


class Crosshair(QtWidgets.QGraphicsItem):
    """
    A QGraphicsItem subclass we can add to a QGraphicsScene to draw a crosshair at a position.
    The crosshair will be drawn with colors inverse of the pixels it is "covering".
    """
    def __init__(self, cross_size, sprite_present, sprite_width, sprite_height):
        QtWidgets.QGraphicsItem.__init__(self)
        self.sprite_present = sprite_present
        self.sprite_height = sprite_height
        self.sprite_width = sprite_width
        self.cross_size = cross_size

        # Number of pixels to draw for each line.
        self.line_len = (self.cross_size * 2) + 1

        # This item is rendered relative to the position set by `setPos()`.
        # As such we can generate the pixel coordinates at which the crosshair will be drawn once.
        # Let's not waste time doing this every time we go to paint as we have enough processing
        # to do during that procedure to determine the color to paint each pixel of the crosshair.
        self.coords = [x for x in self.cross_pixel_range()]

    def boundingRect(self):
        """
        Required method by the `QGraphicsItem` class.
        """
        return Qt.QRectF(-self.cross_size, -self.cross_size, self.cross_size, self.cross_size)

    def cross_pixel_range(self):
        """
        Helper to create an iterable range of values based on the crosshair size.
        Note that the crosshair size is the length of the cross arms, not including the center pixel.
        """
        return range(-self.cross_size, self.cross_size + 1)

    def get_colors(self):
        """
        Retrieve the colors of each pixel from the sprite palette.
        If we have no sprite we return all white as this will be inverted to black.
        The default background of a QGraphicsView seems to be white so a black
        cursor when we have no sprite seems appropriate.
        """
        if self.sprite_present:
            qimage = self.parentItem().pixmap().toImage()

            position = self.pos()

            x_pos = int(position.x())
            y_pos = int(position.y())

            x_colors = [qimage.pixel(x + x_pos, y_pos) for x in self.cross_pixel_range()]
            y_colors = [qimage.pixel(x_pos, y + y_pos) for y in self.cross_pixel_range()]

        else:
            x_colors = y_colors = [(COLOR_MAX, COLOR_MAX, COLOR_MAX, COLOR_MAX)] * self.line_len

        return x_colors, y_colors

    def paint(self, painter, options, widget=None):
        """
        Draw our crosshair. We generate the color-per-pixel and zip it
        together with our coordinates tuple so we can iterate the coordinates with their
        associated colors at the same time.
        """
        x_colors, y_colors = self.get_colors()

        for x, color in zip(self.coords, x_colors):
            painter.setPen(Qt.QPen(inverse_color(color)))
            painter.drawPoint(float(x), 0.0)

        for y, color in zip(self.coords, y_colors):
            painter.setPen(Qt.QPen(inverse_color(color)))
            painter.drawPoint(0.0, float(y))
