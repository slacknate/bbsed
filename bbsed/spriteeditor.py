import io
import os

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import *

from .ui.spriteeditor_ui import Ui_Editor

from .palettedialog import COLOR_BOX_SIZE, PaletteDialog
from .zoomdialog import ZoomDialog
from .util import *


class SpriteEditor(QtWidgets.QWidget):

    data_changed = QtCore.pyqtSignal()

    def __init__(self, mainwindow, paths, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.ui = Ui_Editor()
        self.ui.setupUi(self)

        self.current_sprite = io.BytesIO()
        self.palette_data = io.BytesIO()

        self.mainwindow = mainwindow
        self.paths = paths

        # Create editor related dialogs and associate them to their respective View Menu check items.
        self.zoom_dialog = ZoomDialog(self.mainwindow.ui.view_zoom, parent=mainwindow)
        self.palette_dialog = PaletteDialog(self.mainwindow.ui.view_palette, parent=mainwindow)
        self.palette_dialog.index_selected.connect(self.choose_color_from_index)

        # FIXME: there's something weird about drag select being off by one...
        self.ui.sprite_list.itemSelectionChanged.connect(self.select_sprite)

        # Set up the sprite preview mouse events so we can update various app visuals.
        self.ui.sprite_preview.setMouseTracking(True)
        self.ui.sprite_preview.mouseDoubleClickEvent = self.choose_color_from_coord
        self.ui.sprite_preview.mouseMoveEvent = self.move_zoom_cursor
        self.ui.sprite_preview.enterEvent = self.set_cross_cursor

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

    def _clear_sprite_data(self):
        """
        Reset all graphics views to be blank.
        """
        # Clear our image data.
        self.sprite_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()
        # Clear palette data.
        self.palette_dialog.reset()
        # Clear zoom view.
        self.zoom_dialog.reset()

    def _update_sprite_preview(self):
        """
        Update the sprite preview with the given palette index.
        If no index is provided we assume that the current index is to be used.
        This method is only invoked when we pick a new sprite or select a new palette.
        Our cached sprite uses a palette from the sprite data definition, NOT from the
        in-game palette data. This means that we should always be re-writing the palette.
        """
        character_info, palette_id, slot_info = self.mainwindow.current_selection_info()

        character = character_info[0]
        slot_type = slot_info[0]

        # If we have a saved palette selected we should display that palette.
        if slot_type == PALETTE_SAVE:
            save_name = slot_info[1]
            hpl_files = self.paths.get_saved_palette(character, palette_id, save_name)

        # Otherwise display the edit slot data.
        else:
            hpl_files = self.paths.get_edit_palette(character, palette_id)

        # FIXME: how do we determine which file is for what? e.g. izayoi phorizor?
        #        for now just assume that the first palette is the one that matters, as that is true frequently.
        palette_full_path = hpl_files[0]
        self.palette_data = io.BytesIO()

        try:
            convert_from_hpl(palette_full_path, COLOR_BOX_SIZE, self.palette_data)

        except Exception:
            self.show_error_dialog("Error Setting Palette", "Failed to update the palette image!")
            return

        try:
            # We are only updating the palette data we aren't writing out any pixel information.
            replace_palette(self.current_sprite, palette_full_path)

        except Exception:
            self.show_error_dialog("Error Updating Palette", f"Failed to replace the palette of the current sprite!")

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(self.current_sprite.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        self.sprite_scene.addPixmap(png_pixmap)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

        # Update the dialog palette data since we have switched palettes.
        self.palette_dialog.set_palette(self.palette_data)
        # Update the zoom dialog to the current sprite.
        self.zoom_dialog.set_sprite(self.current_sprite)
        # Do not show the palette or zoom dialogs until after we have set the palette/sprite information on them.
        # If we show them prior to this then the dialog graphics view does not correctly update
        # until we change the current palette.

        # Show our palette dialog if we need to.
        if self.palette_dialog.isHidden():
            self.palette_dialog.show()

        # Show our zoom dialog if we need to.
        if self.zoom_dialog.isHidden():
            self.zoom_dialog.show()

    def update_sprite_preview(self):
        """
        Update the sprite preview but only if a sprite is selected.
        """
        selected_sprite = self.ui.sprite_list.currentItem()
        if selected_sprite is not None:
            self._update_sprite_preview()

    def update_sprite_list(self, character):
        """
        Add image files to the sprite list for the given character.
        """
        with block_signals(self.ui.sprite_list):
            sprite_cache = self.paths.get_sprite_cache(character)
            ui_sprite_cache = [os.path.basename(sprite_full_path) for sprite_full_path in sprite_cache]
            self.ui.sprite_list.addItems(ui_sprite_cache)

    def select_sprite(self):
        """
        A new sprite has been selected.
        Update our image preview with the new sprite.
        """
        character_info, _, __ = self.mainwindow.current_selection_info()
        character = character_info[0]

        selected_sprite = self.ui.sprite_list.currentIndex()

        sprite_cache = self.paths.get_sprite_cache(character)

        list_index = selected_sprite.row()
        hip_full_path = sprite_cache[list_index]
        hip_file = os.path.basename(hip_full_path)

        try:
            self.current_sprite = io.BytesIO()
            convert_from_hip(hip_full_path, self.current_sprite)

        except Exception:
            self.show_error_dialog("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")
            return

        self._update_sprite_preview()

    def move_zoom_cursor(self, evt):
        """
        Move the zoom dialog centerpoint to follow the mouse cursor.
        """
        clicked_point = Qt.QPoint(evt.x(), evt.y())
        mapped_point = self.ui.sprite_preview.mapToScene(clicked_point)
        self.zoom_dialog.move_cursor(mapped_point)

    def _set_color(self, palette_index, color_tuple):
        """
        The color in a palette has been changed by the user.
        Save the changes to disk and update the character visuals live.
        """
        character_info, palette_id, _ = self.mainwindow.current_selection_info()

        character = character_info[0]
        character_name = character_info[1]

        try:
            set_index_color(self.palette_data, palette_index, color_tuple)

        except Exception:
            message = f"Failed to change the color for palette index {palette_index}!"
            self.mainwindow.show_error_dialog("Error Updating Palette", message)
            return

        # FIXME: see other FIXME about HPL files
        hpl_files = self.paths.get_edit_palette(character, palette_id)
        palette_full_path = hpl_files[0]

        try:
            convert_to_hpl(self.palette_data, palette_full_path)

        except Exception:
            message = f"Failed to update palette {palette_id} for {character_name}!"
            self.show_error_dialog("Error Updating Palette", message)
            return

        self.update_sprite_preview()
        self.data_changed.emit()

    def _choose_color(self, palette_index):
        """
        Choose a color for the given palette index.
        Show a QColorDialog to choose the color, with an initial color grabbed from the palette data
        that is associated to the given palette index.
        A bool indicating the dialog accept status and the selected color are returned.
        """
        try:
            current_color = get_index_color(self.palette_data, palette_index)

        except Exception:
            message = f"Failed to fetch the color for palette index {palette_index}!"
            self.show_error_dialog("Error Reading Palette", message)
            return False, ()

        initial = Qt.QColor(*current_color)
        dialog = QtWidgets.QColorDialog(initial, parent=self)
        dialog.setOptions(QtWidgets.QColorDialog.ShowAlphaChannel)

        accepted = dialog.exec_()

        qcolor = dialog.currentColor()
        color_tuple = (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())

        return accepted, color_tuple

    def choose_color_from_index(self, palette_index):
        """
        Pick a color for the given palette index.
        Either the palette dialog was double clicked and emitted `index_selected` or
        the sprite preview was double clicked and we have converted the mouse coordinates
        to a palette index.
        """
        accepted, color_tuple = self._choose_color(palette_index)
        if accepted:
            self._set_color(palette_index, color_tuple)

    def choose_color_from_coord(self, evt):
        """
        We have double clicked on the sprite preview.
        Get the (x, y) coordinate of the click within the graphics view and map it to
        an (x, y) coordinate within the scene (i.e. the sprite image).
        We can use the mapped coordinated to get the palette index of the color we clicked on.
        Finally we can use the palette index to choose a new color.
        """
        x = evt.x()
        y = evt.y()

        mapped_point = self.ui.sprite_preview.mapToScene(Qt.QPoint(x, y))

        try:
            palette_index = get_palette_index(self.current_sprite, (mapped_point.x(), mapped_point.y()))

        except Exception:
            self.show_error_dialog("Error Getting Palette Index", f"Failed to get palette index of selected color!")
            return

        self.choose_color_from_index(palette_index)

    def set_cross_cursor(self, _):
        """
        When we mouse over the sprite set the cursor to a cross.
        """
        self.ui.sprite_preview.viewport().setCursor(QtCore.Qt.CursorShape.CrossCursor)

    def reset(self):
        """
        Reset the editor state.
        We need to clear the sprite list and image data.
        """
        with block_signals(self.ui.sprite_list):
            self.ui.sprite_list.clear()

        self._clear_sprite_data()

    def close_dialogs(self):
        """
        Close both dialogs associated to the editor.
        """
        self.palette_dialog.hide()
        self.zoom_dialog.hide()

    def show_error_dialog(self, *args, **kwargs):
        """
        Wrapper for `MainWindow.show_error_dialog()` solely to save line length.
        """
        self.mainwindow.show_error_dialog(*args, **kwargs)
