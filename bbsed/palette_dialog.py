from PyQt5 import QtCore, Qt, QtWidgets

from .ui.palette_dialog_ui import Ui_Dialog

from .util import block_signals

COLOR_BOX_SIZE = 15
SELECTION_WIDTH = 2

COLOR_MIN = 0
COLOR_MAX = 255

PALLETE_MIN = 0
PALLETE_MAX = 15


def update_channel(channel_val, step):
    """
    Update a color channel value by the given step.
    We ensure the color channel value cannot be less
    than `COLOR_MIN` and not more than `COLOR_MAX`.
    """
    new_channel_val = channel_val + step

    if new_channel_val > COLOR_MAX:
        new_channel_val = COLOR_MAX

    if new_channel_val < COLOR_MIN:
        new_channel_val = COLOR_MIN

    return new_channel_val


def make_selection_rect(pallete_x, pallete_y):
    """
    Helper to create a QGraphicsRectItem for palette index selection(s).
    """
    # To ensure that the QPen-rendered rectangle fits within the palette index square, we need
    # to offset the position and size of the rectangle by a proportion of the width of the rectangle.
    # In this case, it seems like the QPen is rendered centered on the position/size dimensions, so we
    # must shift the position by half the width. Intuitively you would believe we then need to decrease the
    # size by half the width value as well, but due to the position shift we actually have to decrease the size
    # by the entire width value.
    pos_offset = SELECTION_WIDTH // 2
    size_offset = SELECTION_WIDTH

    x = pallete_x * COLOR_BOX_SIZE + pos_offset
    y = pallete_y * COLOR_BOX_SIZE + pos_offset

    rect_pen = Qt.QPen(Qt.QColorConstants.Red)
    rect_pen.setWidth(SELECTION_WIDTH)

    rect_item = Qt.QGraphicsRectItem(x, y, COLOR_BOX_SIZE - size_offset, COLOR_BOX_SIZE - size_offset)
    rect_item.setPen(rect_pen)

    return rect_item


def get_range_dimensions(index_range):
    """
    Get the dimensions of a palette index range.
    Used to compare two ranges to determine if they are of equal size.
    """
    num_columns = len(set(i[0] for i in index_range))
    num_rows = len(set(i[1] for i in index_range))
    return num_columns, num_rows


def compare_ranges(index_range1, index_range2):
    """
    Determine if two palette index ranges are of equal size.
    """
    col1, row1 = get_range_dimensions(index_range1)
    col2, row2 = get_range_dimensions(index_range2)
    return col1 == col2 and row1 == row2


class ColorSelection:
    """
    Helper object to track the palette indices and their respective colors
    that are to be used by a cut/copy operation when we paste.
    This ensures we get the colors at the time of the cut/copy even if those
    palette colors are changed before we paste.
    """
    def __init__(self, index_selection, color_selection):
        self.index_selection = index_selection
        self.color_selection = color_selection

    def compare(self, comp_selection):
        """
        Compare an index selection range to the range tracked by this object.
        """
        return compare_ranges(self.index_selection, comp_selection)

    def get_paste(self, dst_range):
        """
        Helper to get an indices changed list we can pass to the PaletteDialog signal.
        """
        selection_order = zip(self.index_selection, self.color_selection)

        # Ensure our color selection is sorted least to greatest by selection index and that
        # the destination range is also sorted least to greatest by selection index. This ensures
        # that when we paste the color selection that the colors will be inserted in least to
        # greatest order as well, which is intuitively how a user would expect paste to function.
        color_selection = [_item[1] for _item in sorted(selection_order, key=lambda __item: __item[0])]
        dst_range = sorted(dst_range)

        return list(zip(dst_range, color_selection))


class PaletteDialog(QtWidgets.QDialog):

    index_selected = QtCore.pyqtSignal(tuple)
    indices_changed = QtCore.pyqtSignal(list)

    def __init__(self, sprite, menu_check, parent=None):
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        QtWidgets.QDialog.__init__(self, parent, flags=flags)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Palette Data")
        self.mainwindow = parent
        self.sprite = sprite

        self.menu_check = menu_check
        self.menu_check.triggered.connect(self.setVisible)

        # Set up our palette viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.palette_scene = QtWidgets.QGraphicsScene()
        self.ui.png_view.setScene(self.palette_scene)

        # Set up mouse event handlers.
        # Without invoking self.ui.png_view.setMouseTracking(True) the mouseMoveEvent only
        # applies to drag events and not button-less motion.
        self.ui.png_view.mousePressEvent = self.mouse_press_event
        self.ui.png_view.mouseMoveEvent = self.mouse_move_event
        self.ui.png_view.mouseDoubleClickEvent = self.mouse_double_click_event

        # Setup toolbar actions that are pertinent to the palette dialog.
        self.mainwindow.ui.cut_color.triggered.connect(self.cut_color)
        self.mainwindow.ui.copy_color.triggered.connect(self.copy_color)
        self.mainwindow.ui.paste_color.triggered.connect(self.paste_color)
        self.mainwindow.ui.fill_color.triggered.connect(self.fill_color)
        self.mainwindow.ui.swap_color.triggered.connect(self.swap_color)
        self.mainwindow.ui.gradient_color.triggered.connect(self.gradient_color)
        self.set_tool_enable(False)

        self.index_selection_range = [None, None]
        self.index_selection_items = []

        self.src_colors = None
        self.swap_info = None

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

    def iter_index_range(self):
        """
        Helper to iterate a palette index selection range based on a start and end index.
        Our selection may have to step in reverse depending on the way the mouse has been click-dragged.
        This can occur independently for both axes, and we do some quick maths to determine which way
        we must step in order to select the correct palette indices.
        """
        start, end = self.index_selection_range

        start_x, start_y = start
        end_x, end_y = end

        step_x = 1
        if end_x - start_x < 0:
            step_x = -1

        step_y = 1
        if end_y - start_y < 0:
            step_y = -1

        for palette_y in range(start_y, end_y + step_y, step_y):
            for palette_x in range(start_x, end_x + step_x, step_x):
                yield palette_x, palette_y

    def refresh_canvas(self):
        """
        Ensure the graphics view is refreshed so changes are visible to the user.
        """
        self.ui.png_view.viewport().update()

    def refresh_items(self):
        """
        Refresh our palette scene.
        We may or may not have selection changes that need to be displayed.
        """
        if self.index_selection_range != [None, None]:
            for palette_x, palette_y in self.iter_index_range():
                rect_item = make_selection_rect(palette_x, palette_y)
                self.index_selection_items.append(rect_item)

        for rect_item in self.index_selection_items:
            self.palette_scene.addItem(rect_item)

        self.refresh_canvas()

    def set_tool_enable(self, state):
        """
        Set the enable state of the toolbar actions that are relevant to the palette dialog.
        """
        self.mainwindow.ui.cut_color.setEnabled(state)
        self.mainwindow.ui.copy_color.setEnabled(state)
        self.mainwindow.ui.paste_color.setEnabled(state)
        self.mainwindow.ui.fill_color.setEnabled(state)
        self.mainwindow.ui.swap_color.setEnabled(state)
        self.mainwindow.ui.gradient_color.setEnabled(state)

    def clear_selection(self):
        """
        Set our selection range back to "no selection" and remove all selection graphics items from our scene.
        """
        self.set_tool_enable(False)

        for rect_item in self.index_selection_items:
            self.palette_scene.removeItem(rect_item)

        self.index_selection_range = [None, None]
        self.index_selection_items = []

        self.refresh_canvas()

    def mouse_press_event(self, evt):
        """
        On left-clicks we make an initial palette index selection.
        Other mouse buttons simply clear the selection.
        """
        self.clear_selection()

        # Only set a palette index selection for left click.
        # We want the user to be able to clear the selection with other mouse buttons.
        if evt.button() == QtCore.Qt.MouseButton.LeftButton:
            pallete_x = evt.x() // COLOR_BOX_SIZE
            pallete_y = evt.y() // COLOR_BOX_SIZE

            palette_index = (pallete_x, pallete_y)

            # If we have an active swap in process we should perform it.
            # In that case we return early as swap selections are a singular index,
            # and we do not need to make a "full" selection to complete this operation.
            # We also do not want to be layering operations, i.e. making a selection with
            # which we can use the palette editing tools while a swap is in progress as
            # that is not an intuitive flow and also makes this complicated.
            if self.swap_info is not None:
                self.do_swap(palette_index)
                return

            self.index_selection_range[0] = palette_index
            self.index_selection_range[1] = palette_index

            self.set_tool_enable(True)

        self.refresh_items()

    def mouse_move_event(self, evt):
        """
        On left-click drag we want to set an ending index selection.
        This is used to define our selection range, which in turn generates the
        graphics items to display the selection visually.
        """
        # Do a check to ensure that if we somehow accidentally enable button-less mouse motion
        # handling that the app will not explode. We do not want to set an end index if no start
        # has been selected.
        if self.index_selection_range != [None, None]:
            # If we have an existing selection range we need to clear any graphics items so we can
            # draw the new selection without having duplicate items.
            for rect_item in self.index_selection_items:
                self.palette_scene.removeItem(rect_item)

            pallete_x = evt.x() // COLOR_BOX_SIZE
            pallete_y = evt.y() // COLOR_BOX_SIZE

            # Reset the selection items and set the send of our selection range.
            # When we subsequently refresh we will generate a new set of graphics items.
            self.index_selection_items = []
            if PALLETE_MIN <= pallete_x <= PALLETE_MAX and PALLETE_MIN <= pallete_y <= PALLETE_MAX:
                self.index_selection_range[1] = (pallete_x, pallete_y)

            self.refresh_items()

    def mouse_double_click_event(self, evt):
        """
        Event handler for double clicks on the palette view.
        We emit a signal to let the sprite editor know we have double clicked on the
        palette dialog and want to pick a color for the given palette index.
        """
        # Only emit `index_selected` on left double-click.
        if evt.button() == QtCore.Qt.MouseButton.LeftButton:
            palette_x = evt.x() // COLOR_BOX_SIZE
            palette_y = evt.y() // COLOR_BOX_SIZE

            self.index_selected.emit((palette_x, palette_y))

    def cut_color(self):
        """
        Cut colors from the current selection range and store them in our source colors buffer.
        We replace the cut colors with solid black.
        """
        cut_range = list(self.iter_index_range())
        cut_colors = self.sprite.get_index_color_range(*cut_range)
        self.src_colors = ColorSelection(cut_range, cut_colors)

        index_colors = []
        for palette_index in cut_range:
            index_colors.append((palette_index, (COLOR_MIN, COLOR_MIN, COLOR_MIN, COLOR_MAX)))

        self.indices_changed.emit(index_colors)

    def copy_color(self):
        """
        Copy the colors from the current selection range and store them in our source colors buffer.
        """
        copy_range = list(self.iter_index_range())
        copied_colors = self.sprite.get_index_color_range(*copy_range)
        self.src_colors = ColorSelection(copy_range, copied_colors)

    def paste_color(self):
        """
        Paste the colors from a previous cut/copy operation.
        """
        dst_range = list(self.iter_index_range())

        if not self.src_colors.compare(dst_range):
            message = "Destination selection must be the same dimensions as source selection!"
            self.mainwindow.show_message_dialog("Paste Error", message, icon="error")
            return

        index_colors = self.src_colors.get_paste(dst_range)
        self.indices_changed.emit(index_colors)

    def fill_color(self):
        """
        Fill currently selected indices with a selected color.
        """
        dialog = QtWidgets.QColorDialog(parent=self)
        dialog.setOptions(QtWidgets.QColorDialog.ShowAlphaChannel)

        accepted = dialog.exec_()
        if accepted:
            qcolor = dialog.currentColor()
            color_tuple = (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())

            index_colors = []
            for palette_index in self.iter_index_range():
                index_colors.append((palette_index, color_tuple))

            self.indices_changed.emit(index_colors)

    def swap_color(self):
        """
        If we have a singular selected index mark it as our swap index.
        When we next make a selection it will be swapped with that index.
        """
        swap_range = list(self.iter_index_range())

        if len(swap_range) > 1:
            message = "Destination selection must be the same dimensions as source selection!"
            self.mainwindow.show_message_dialog("Paste Error", message, icon="error")
            return

        swap_index = swap_range[0]
        swap_color = self.sprite.get_index_color(swap_index)

        self.swap_info = (swap_index, swap_color)

    def do_swap(self, swap_index2):
        """
        We have made a selection with an active swap selected.
        Create an indices changes list and emit the signal.
        We also reset our swap info to `None` as the swap is complete.
        """
        swap_color2 = self.sprite.get_index_color(swap_index2)

        swap_index, swap_color = self.swap_info
        self.swap_info = None

        index_colors = [(swap_index, swap_color2), (swap_index2, swap_color)]
        self.indices_changed.emit(index_colors)

    def gradient_color(self):
        """
        Generate a color gradient that starts at the first selected palette index
        and ends at the last selected palette index. The color gradient will overwrite
        all selected colors with the gradient, and the generated gradient shifts from
        the first color to the last which each step.
        """
        gradient_range = list(self.iter_index_range())
        num_steps = len(gradient_range)

        start_index = gradient_range[0]
        start_color = tuple(self.sprite.get_index_color(start_index))

        end_index = gradient_range[-1]
        end_color = tuple(self.sprite.get_index_color(end_index))
        # FIXME: pretty sure we do not always get to the end color...

        r_delta = end_color[0] - start_color[0]
        g_delta = end_color[1] - start_color[1]
        b_delta = end_color[2] - start_color[2]
        a_delta = end_color[3] - start_color[3]

        r_round = -1 if r_delta < 0 else 1
        g_round = -1 if g_delta < 0 else 1
        b_round = -1 if b_delta < 0 else 1
        a_round = -1 if a_delta < 0 else 1

        r_step = (r_delta + r_round) // num_steps
        g_step = (g_delta + g_round) // num_steps
        b_step = (b_delta + b_round) // num_steps
        a_step = (a_delta + a_round) // num_steps

        r, g, b, a = start_color
        index_colors = []

        for palette_index in gradient_range:
            index_colors.append((palette_index, (r, g, b, a)))
            r = update_channel(r, r_step)
            g = update_channel(g, g_step)
            b = update_channel(b, b_step)
            a = update_channel(a, a_step)

        self.indices_changed.emit(index_colors)

    def set_palette(self, palette_image):
        """
        Load a palette from file and display the data in the dialog.
        """
        # Reset the index selection as we are loading a new palette and thus our selection, if it exists, is invalid.
        self.clear_selection()

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(palette_image, "PNG")

        # Clear our image date and load in the updates image data.
        self.palette_scene.clear()
        self.palette_scene.addPixmap(png_pixmap)

        self.refresh_items()
