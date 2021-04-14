import io
import os

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import *

from .ui.spriteeditor_ui import Ui_Editor

from .palettedialog import COLOR_BOX_SIZE, PaletteDialog
from .zoomdialog import ZoomDialog
from .crosshair import Crosshair
from .char_info import *
from .util import *

CROSS_HAIR_SIZE = 20


class SpriteEditor(QtWidgets.QWidget):

    image_data_changed = QtCore.pyqtSignal()
    character_changed = QtCore.pyqtSignal(str, str)
    palette_changed = QtCore.pyqtSignal(str, str)
    palette_slot_changed = QtCore.pyqtSignal(str, int)

    def __init__(self, mainwindow, paths, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.ui = Ui_Editor()
        self.ui.setupUi(self)

        self.palette_data = io.BytesIO()
        self.current_sprite = io.BytesIO()

        self.crosshair = Crosshair(CROSS_HAIR_SIZE, False, 0, 0)

        self.mainwindow = mainwindow
        self.paths = paths

        # We need to sort the character info before adding to the selection combo box.
        # This way the combo box index will match the defined character IDs in the char_info module.
        sorted_chars = list(CHARACTER_INFO.items())
        sorted_chars.sort(key=lambda item: item[0])

        for _, (character_name, character) in sorted_chars:
            self.ui.char_select.addItem(character_name, character)

        self.ui.char_select.setCurrentIndex(-1)
        self.ui.char_select.currentIndexChanged.connect(self.select_character)
        self.ui.palette_select.currentIndexChanged.connect(self.select_palette)
        self.ui.slot_select.currentIndexChanged.connect(self.select_palette_slot)

        # Create editor related dialogs and associate them to their respective View Menu check items.
        self.zoom_dialog = ZoomDialog(self.mainwindow.ui.view_zoom, parent=mainwindow)
        self.palette_dialog = PaletteDialog(self.mainwindow.ui.view_palette, parent=mainwindow)
        self.palette_dialog.index_selected.connect(self.choose_color_from_index)

        # FIXME: the sprite list misses the first selection changed if the user drags the mouse without
        #        releasing it. can we just disallow this? and what do we replace it right?
        self.ui.sprite_list.setSelectionMode(QtWidgets.QListWidget.SelectionMode.SingleSelection)
        self.ui.sprite_list.itemSelectionChanged.connect(self.select_sprite)

        # Set up the sprite preview mouse events so we can update various app visuals.
        self.ui.sprite_preview.setMouseTracking(True)
        self.ui.sprite_preview.mouseDoubleClickEvent = self.choose_color_from_coord
        self.ui.sprite_preview.mouseMoveEvent = self.mouse_move_event
        # Do not show a cursor as we are going to be manually drawing a cursor. Why?
        # I am not happy with the CrossCursor that is built into Qt, and we have to implement
        # a way to draw a crosshair for the Zoom Dialog anyway.
        self.ui.sprite_preview.viewport().setCursor(QtCore.Qt.CursorShape.BlankCursor)

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

    def get_character(self):
        """
        Get the name and character ID of the current selected character.
        """
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()
        return character_name, character

    def find_character(self, character_name=None, character=None):
        """
        Find a character. We allow for finding a character via name or by abbreviation.
        """
        character_id = -1

        if character_name is None and character is None:
            raise ValueError("Must provide either a character name or a character abbreviation!")

        if character_name:
            character_id = self.ui.char_select.findText(character_name)

        if character:
            character_id = self.ui.char_select.findData(character)

        return CHARACTER_INFO[character_id]

    def get_palette(self):
        """
        Get the palette ID and palette number of the current selected palette.
        A palette ID is the number displayed in game, a palette number is the number used in the files on disk.
        """
        palette_id = self.ui.palette_select.currentText()
        palette_num = self.ui.palette_select.currentData()
        return palette_id, palette_num

    def get_slot(self):
        """
        Get the palette slot name and slot typeof the current selected palette slot.
        """
        slot_name = self.ui.slot_select.currentText()
        slot_type = self.ui.slot_select.currentData()
        return slot_name, slot_type

    def set_slot(self, slot_name=None, slot_type=None):
        """
        Set the current palette slot. We allow for setting by name or type.
        """
        slot_index = -1

        if slot_name is None and slot_type is None:
            raise ValueError("Must provide either a slot name or a slot type!")

        if slot_name:
            slot_index = self.ui.slot_select.findText(slot_name)

        if slot_type:
            slot_index = self.ui.slot_select.findData(slot_type)

        self.ui.slot_select.setCurrentIndex(slot_index)

    def delete_slot(self, save_name):
        """
        We have deleted the save slot identified by `save_name`. We should remove it from the UI.
        """
        save_index = self.ui.slot_select.findText(save_name)

        with block_signals(self.ui.slot_select):
            self.ui.slot_select.removeItem(save_index)

        # Re-select the edit slot after we delete a palette.
        self.ui.slot_select.setCurrentIndex(0)

    def import_palette_data(self, character, palette_id, hpl_to_import, pac_to_import):
        """
        We have successfully imported palette data. Update the UI to include the new palettes if applicable.
        """
        with block_signals(self.ui.slot_select):
            for save_char, save_pal_id, save_name in hpl_to_import.keys():
                if save_char == character and save_pal_id == palette_id:
                    self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

            for file_info in pac_to_import.values():
                for save_char, save_pal_id, save_name in file_info.keys():
                    if save_char == character and save_pal_id == palette_id:
                        self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

    def add_save_slot(self, slot_name):
        """
        We have saved a palette. Add the slot name to the UI if necessary and select the slot.
        """
        # We may be saving changes made to a palette that already has a save name.
        save_index = self.ui.slot_select.findText(slot_name)

        with block_signals(self.ui.slot_select):
            # Only add a new item if this save name is new.
            # This will happen if the palette has not been saved before
            # or if the user has selected the "Save As" option.
            if save_index < 0:
                self.ui.slot_select.addItem(slot_name, PALETTE_SAVE)
                save_index = self.ui.slot_select.findText(slot_name)

            self.ui.slot_select.setCurrentIndex(save_index)

        # If this is the first palette saved for this character and palette ID then we will need to enable
        # the save select combobox.
        if not self.ui.slot_select.isEnabled():
            self.ui.slot_select.setEnabled(True)

    def _update_save_slots(self, character_saves):
        """
        We have selected a character or a palette.
        We need to update the available slots presented in the UI.
        """
        with block_signals(self.ui.slot_select):
            # Clearing the save select and re-adding items will auto-select the first item
            # which will always be a non-saved palette.
            self.ui.slot_select.clear()
            self.ui.slot_select.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

            # Set the save select enable state based on the presence of files on disk.
            self.ui.slot_select.setEnabled(bool(character_saves))
            for save_name in character_saves:
                self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

    def select_character(self):
        """
        A new character was picked from the character combobox.
        Note that we explicity DO NOT update the sprite list here.
        We need to wait for the mainwindow to perform sprite extraction (if necessary)
        and after that completes the mainwindow will invoke `SpritEditor.update_sprite_list()`.
        """
        self.reset()

        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()

        # Don't allow the user to interact with these parts of the UI while we are updating them.
        self.ui.sprite_group.setEnabled(False)

        # Block signals while we add items so the signals are not emitted.
        # We do not want to try to select a palette before a sprite is selected, and
        # at the very least we do not want to spam the signals in a loop regardless.
        with block_signals(self.ui.palette_select):
            for palette_num in range(GAME_MAX_PALETTES):
                palette_id = palette_number_to_id(palette_num)
                self.ui.palette_select.addItem(palette_id)

            # Automatically select the first palette.
            # We intentionally select this in the block_signals block so we do not try to set
            # palette data before a sprite is selected.
            self.ui.palette_select.setCurrentIndex(0)

        # Get the palette ID from the widget for the sake of consistency.
        palette_id = self.ui.palette_select.currentText()

        # Update the UI to show any save slots for the first palette.
        character_saves = self.paths.get_character_saves(character, palette_id)
        self._update_save_slots(character_saves)

        # Re-enable user interaction for everything else.
        self.ui.sprite_group.setEnabled(True)

        self.character_changed.emit(character_name, character)

    def select_palette(self):
        """
        A new palette has been selected.
        Replace the palette of the currently selected sprite and update the image preview.
        """
        character = self.ui.char_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        palette_num = self.ui.palette_select.currentData()

        # When we select a palette ID we need to look for existing saved palettes associated to it.
        # Based on the presence of these files we also need to update the state of the UI.
        character_saves = self.paths.get_character_saves(character, palette_id)
        self._update_save_slots(character_saves)

        self.update_sprite_preview()

        self.palette_changed.emit(palette_id, palette_num)

    def select_palette_slot(self):
        """
        We have selected a palette which has been saved by the user.
        Disable the delete button when we have the Edit slot selected.
        """
        slot_name = self.ui.slot_select.currentText()
        slot_type = self.ui.slot_select.currentData()

        self.update_sprite_preview()

        self.palette_slot_changed.emit(slot_name, slot_type)

    def _clear_sprite_data(self):
        """
        Reset all graphics views to be blank.
        """
        # Clear our image data.
        self.current_sprite = io.BytesIO()
        self.sprite_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()
        # Clear palette data.
        self.palette_data = io.BytesIO()
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
        character = self.ui.char_select.currentData()
        slot_name = self.ui.slot_select.currentText()
        slot_type = self.ui.slot_select.currentData()
        palette_id = self.ui.palette_select.currentText()

        # If we have a saved palette selected we should display that palette.
        if slot_type == PALETTE_SAVE:
            save_name = slot_name
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

        # We need a new crosshair every time we clear the scene.
        # We have updated the sprite data anyway so it makes sense to recreate it.
        self.crosshair = Crosshair(CROSS_HAIR_SIZE, True, png_pixmap.width(), png_pixmap.height())

        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        pixmap_item = self.sprite_scene.addPixmap(png_pixmap)
        self.sprite_scene.addItem(self.crosshair)

        # Set the parent item of the crosshair to the added png pixmap so the crosshair can
        # determine what color it should be drawn using the pixmap as a reference.
        self.crosshair.setParentItem(pixmap_item)

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
        character = self.ui.char_select.currentData()

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

    def mouse_move_event(self, evt):
        """
        Move the zoom dialog centerpoint to follow the mouse cursor.
        """
        motion_point = Qt.QPoint(evt.x(), evt.y())
        mapped_point = self.ui.sprite_preview.mapToScene(motion_point)
        self.zoom_dialog.move_cursor(mapped_point)
        self.crosshair.setPos(mapped_point)
        # Ensure the graphics view is refreshed so our crosshair colors update.
        self.ui.sprite_preview.viewport().update()

    def _set_color(self, palette_index, color_tuple):
        """
        The color in a palette has been changed by the user.
        Save the changes to disk and update the character visuals live.
        """
        palette_id = self.ui.palette_select.currentText()
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()

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
        self.image_data_changed.emit()

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

    def reset(self):
        """
        Reset the editor state.
        We need to clear the sprite list and image data.
        """
        with block_signals(self.ui.char_select):
            self.ui.char_select.setCurrentIndex(-1)

        with block_signals(self.ui.palette_select):
            self.ui.palette_select.setCurrentIndex(-1)

        with block_signals(self.ui.slot_select):
            self.ui.slot_select.setEnabled(False)
            self.ui.slot_select.clear()
            self.ui.slot_select.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

        with block_signals(self.ui.sprite_list):
            self.ui.sprite_list.clear()

        self._clear_sprite_data()

    def set_selection_enable(self, state):
        """
        Set the enable state of the character group.
        Used to enable or disable the character, palette, and slot selection widgets.
        """
        self.ui.character_group.setEnabled(state)

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
