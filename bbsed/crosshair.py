from PyQt5 import Qt, QtWidgets

from libhpl import get_palette_index_range, get_index_color_range

COLOR_MAX = 255


def inverse_color(color_tuple):
    """
    Return the inverse color of the given color.
    We ignore transparency as a crosshair should always be fully opaque.
    """
    r, g, b, _ = color_tuple
    return Qt.QColor(COLOR_MAX - r, COLOR_MAX - g, COLOR_MAX - b, COLOR_MAX)


# FIXME: this needs to be more efficient
class Crosshair(QtWidgets.QGraphicsItem):
    """
    A QGraphicsItem subclass we can add to a QGraphicsScene to draw a crosshair at a position.
    The crosshair will be drawn with colors inverse of the pixels it is "covering".
    """
    def __init__(self, cross_size, sprite_data, sprite_width, sprite_height):
        QtWidgets.QGraphicsItem.__init__(self)
        self.sprite_height = sprite_height
        self.sprite_width = sprite_width
        self.sprite_data = sprite_data
        self.cross_size = cross_size

        # Number of pixels to draw for each line.
        self.line_len = (self.cross_size * 2) + 1

        # This item is rendered relative to the position set by `setPos()`.
        # As such we can generate the pixel coordinates at which the crosshair will be drawn once.
        # Let's not waste time doing this every time we go to paint as we have enough processing
        # to do during that procedure to determine the color to paint each pixel of the crosshair.
        self.x_coords = [(x, 0) for x in self.cross_pixel_range()]
        self.y_coords = [(0, y) for y in self.cross_pixel_range()]

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

    def get_x_colors(self, x_pos, y_pos):
        y_valid = (0 <= y_pos < self.sprite_height)

        x_invalid = 0
        x_coords = []
        x_colors = []

        for x in self.cross_pixel_range():
            x_actual = x + x_pos

            if x_actual < 0 or not y_valid:
                x_invalid = -1

            if x_actual >= self.sprite_width or not y_valid:
                x_invalid = 1

            if 0 <= x_actual < self.sprite_width and y_valid:
                x_coords.append((x_actual, y_pos))

        if x_coords:
            x_indicies = get_palette_index_range(self.sprite_data, *x_coords)
            x_colors = get_index_color_range(self.sprite_data, *x_indicies)

        white_pixels = [(COLOR_MAX, COLOR_MAX, COLOR_MAX, COLOR_MAX)] * (self.line_len - len(x_coords))

        if x_invalid < 0:
            x_colors = white_pixels + x_colors

        if x_invalid > 0:
            x_colors = x_colors + white_pixels

        return x_colors

    def get_y_colors(self, x_pos, y_pos):
        x_valid = (0 <= x_pos < self.sprite_width)

        y_invalid = 0
        y_coords = []
        y_colors = []

        for y in self.cross_pixel_range():
            y_actual = y + y_pos

            if y_actual < 0 or not x_valid:
                y_invalid = -1

            if y_actual >= self.sprite_height or not x_valid:
                y_invalid = 1

            if 0 <= y_actual < self.sprite_height and x_valid:
                y_coords.append((x_pos, y_actual))

        if y_coords:
            y_indicies = get_palette_index_range(self.sprite_data, *y_coords)
            y_colors = get_index_color_range(self.sprite_data, *y_indicies)

        white_pixels = [(COLOR_MAX, COLOR_MAX, COLOR_MAX, COLOR_MAX)] * (self.line_len - len(y_colors))

        if y_invalid < 0:
            y_colors = white_pixels + y_colors

        if y_invalid > 0:
            y_colors = y_colors + white_pixels

        return y_colors

    def get_colors(self):
        """
        Retrieve the colors of each pixel from the sprite palette.
        If we have no sprite we return all white as this will be inverted to black.
        The default background of a QGraphicsView seems to be white so a black
        cursor when we have no sprite seems appropriate.
        """
        if self.sprite_data:
            position = self.pos()

            x_pos = int(position.x())
            y_pos = int(position.y())

            x_colors = self.get_x_colors(x_pos, y_pos)
            y_colors = self.get_y_colors(x_pos, y_pos)

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

        for (x, _), color in zip(self.x_coords, x_colors):
            painter.setPen(Qt.QPen(inverse_color(color)))
            painter.drawPoint(float(x), 0.0)

        for (_, y), color in zip(self.y_coords, y_colors):
            painter.setPen(Qt.QPen(inverse_color(color)))
            painter.drawPoint(0.0, float(y))
