import io
import os

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import replace_palette

from .ui.selectdialog_ui import Ui_Dialog

from .exceptions import AppError
from .char_info import CHARACTER_INFO
from .util import *

ROLE_SLOT_TYPE = QtCore.Qt.ItemDataRole.UserRole
ROLE_CHECK_STATE = QtCore.Qt.ItemDataRole.UserRole + 1

PALETTE_GROUP_PREFIX = "palette_{}"
SELECT_COMBOBOX_PREFIX = "select_{}"
SELECT_CHECK_PREFIX = "check_{}"


def normalize_index(select_index):
    """
    If we have discarded the edits or deleted saves that were selected here previously then
    we will not have added a corresponding slot to the combo box and when we look for the relevant
    data/text it will not be found. In this case the index returned will be negative.
    If we no longer have edits we fall back to the "No Palette" slot.
    """
    if select_index < 0:
        select_index = 0

    return select_index


class SelectDialog(QtWidgets.QDialog):
    def __init__(self, paths, config=None, allow_multi_select=False, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.paths = paths
        self.config = config
        self.allow_multi_select = allow_multi_select
        self.selected_palettes = set()
        self.updated = {}

        self.setWindowTitle("Select Palettes")

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        self.current_sprite = io.BytesIO()

        # We need to sort the character info before adding to the selection combo box.
        # This way the combo box index will match the defined character IDs in the char_info module.
        sorted_chars = list(CHARACTER_INFO.items())
        sorted_chars.sort(key=lambda item: item[0])

        # Set up the character selection.
        with block_signals(self.ui.character_select):
            for _, (character_name, character) in sorted_chars:
                self.ui.character_select.addItem(character_name, character)

            self.ui.character_select.currentIndexChanged.connect(self.select_character)
            self.ui.character_select.setCurrentIndex(-1)

        def _update_multislot_callback(_palette_id, _select_combo):
            """
            Create a callback to update the check state of the multi-select checkbox.
            """
            return lambda _check_state: self.update_check_state(_palette_id, _check_state, _select_combo)

        def _update_preview_callback(_palette_id, _select_check, _select_combo):
            """
            Create a callback to update the sprite preview that works with any Qt signal.
            """
            return lambda *_, **__: self.update_sprite_preview(_palette_id, _select_check, _select_combo)

        for palette_id, palette_group, select_check, select_combo in self.iter_widgets():
            # If we allow for selecting multiple palettes per slot we need to set up a
            # signal to update the state of the checkbox for each combobox item.
            if self.allow_multi_select:
                select_check.stateChanged.connect(_update_multislot_callback(palette_id, select_combo))
            # Otherwise hide the checkbox and don't worry about signals.
            else:
                select_check.hide()

            callback = _update_preview_callback(palette_id, select_check, select_combo)
            # We want combo box selections to update the sprite preview.
            select_combo.currentIndexChanged.connect(callback)
            # We also want to be able to easily change palette preview by clicking a palette group box.
            palette_group.mousePressEvent = callback

    def accept(self):
        QtWidgets.QDialog.accept(self)
        # Only update a backend config for this dialog if it exists.
        if self.config is not None:
            self.config.update(**self.updated)

    def iter_widgets(self):
        """
        Helper to iterate our palette selection widgets.
        """
        for palette_number in range(GAME_MAX_PALETTES):
            palette_id = palette_number_to_id(palette_number)

            # The attribute names of these widgets are explicitly defined in Qt Designer.
            # These attributes will in fact exist and we get at them this way to avoid writing a giant block of
            # code that would manually call out these widgets `GAME_MAX_PALETTES` times.
            palette_group = getattr(self.ui, PALETTE_GROUP_PREFIX.format(palette_id))
            select_check = getattr(self.ui, SELECT_CHECK_PREFIX.format(palette_id))
            select_combo = getattr(self.ui, SELECT_COMBOBOX_PREFIX.format(palette_id))

            yield palette_id, palette_group, select_check, select_combo

    def select_character(self):
        """
        A character was selected.
        We populate the palette selection widgets to reflect selections that were previously
        made and applied to the game for this character, as well as any saved palettes and current edits.
        """
        if not self.ui.palette_pages.isEnabled():
            self.ui.palette_pages.setEnabled(True)

        character = self.ui.character_select.currentData()
        sprites_are_extracted = bool(self.paths.get_sprite_cache(character))

        for palette_id, _, select_check, select_combo in self.iter_widgets():
            palettes_are_extracted = bool(self.paths.get_edit_palette(character, palette_id))

            with block_signals(select_combo):
                select_combo.clear()

                # Allow the user to choose not to change this palette in game.
                # Note that if we are in multi-select mode we do not add this slot.
                # In multi-select mode the "No Palette" equivalent is not setting the check for any slots.
                if not self.allow_multi_select:
                    select_combo.addItem(SLOT_NAME_NONE, PALETTE_NONE)
                    select_combo.setItemData(0, False, ROLE_CHECK_STATE)

                # Only show the edit slot if sprites and palettes have been extracted
                # We have encounter a scenario where someone imports palettes without
                # editing or extracting any palettes on their own.
                if sprites_are_extracted and palettes_are_extracted:
                    select_combo.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)
                    index = select_combo.findText(SLOT_NAME_EDIT)
                    select_combo.setItemData(index, False, ROLE_CHECK_STATE)

                # Show any saved palettes that map to this palette ID.
                character_saves = self.paths.get_character_saves(character, palette_id)
                for save_name in character_saves:
                    select_combo.addItem(save_name, PALETTE_SAVE)
                    index = select_combo.findText(save_name)
                    select_combo.setItemData(index, False, ROLE_CHECK_STATE)

                # We do not require the select dialog to have a backed configuration that remembers
                # previously selected palettes. If such a config was not provided, we have no work to do here.
                if self.config is not None:  # TODO: multi-select compatibility?
                    select_name = self._get_palette_selected(character, palette_id)
                    is_checked = False  # LOL

                    # If the config data is the "No Palette" value we pick the first item.
                    # The first item in the selection combobox will always be the "No Palette" option
                    # if we are not working in multi-select mode.
                    if select_name in (SLOT_NAME_NONE,):
                        select_combo.setCurrentIndex(0)
                        slot_type = PALETTE_NONE

                    # If the config data called out the edit slot we need to look for an associated edit slot.
                    elif select_name in (SLOT_NAME_EDIT,):
                        index = select_combo.findData(PALETTE_EDIT)
                        select_combo.setCurrentIndex(normalize_index(index))
                        slot_type = PALETTE_EDIT

                    # Otherwise we are working with a save name and need to ask the combo box what index is associated.
                    else:
                        index = select_combo.findText(select_name)
                        select_combo.setCurrentIndex(normalize_index(index))
                        slot_type = PALETTE_SAVE

                    # Update the selected state of this palette.
                    self._mark_palette_selected(character, palette_id, select_name, slot_type, is_checked)

    def _update_sprite_preview(self, sprite_cache, character, palette_id, select_name):
        """
        A character selection or palette selection was made and
        we need to update the UI to show the most relevant preview.
        """
        # Get the first sprite from our cache to show as a preview.
        # We don't really need to provide options here as this is a quick preview.
        hip_full_path = sprite_cache[0]

        try:
            self.current_sprite = io.BytesIO()
            convert_from_hip(hip_full_path, self.current_sprite)

        except Exception:
            hip_file = os.path.basename(hip_full_path)
            self.parent().show_error_dialog("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")
            return

        if select_name == SLOT_NAME_EDIT:
            hpl_files = self.paths.get_edit_palette(character, palette_id)
        else:
            hpl_files = self.paths.get_saved_palette(character, palette_id, select_name)

        # FIXME: the typical HPL assumption :(
        palette_full_path = hpl_files[0]

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

    def _get_palette_selected(self, character, palette_id):
        """
        Get the palette selection from our apply config file data.
        """
        return getattr(self.config, character + "_" + palette_id)  # TODO: multi-select compatibility?

    def _mark_palette_selected(self, character, palette_id, select_name, slot_type, is_checked):
        """
        Update our selections that will be saved to disk in the apply config as well as
        the selections data we use to generate the data to apply to game files.
        Note that if the dialog is not accepted these datas are discarded.
        """
        select_key = (character, palette_id, select_name)

        # Only update the data that we may want to save to disk if the config to do has has been provided.
        if self.config is not None:  # TODO: multi-select compatibility?
            self.updated[character + "_" + palette_id] = select_name

        if self.allow_multi_select:
            is_selected = is_checked
        else:
            is_selected = slot_type != PALETTE_NONE

        if is_selected:
            self.selected_palettes.add(select_key)
        else:
            self.selected_palettes.discard(select_key)

    def update_check_state(self, palette_id, check_state, select_combo):
        """
        Update the state of our multi-select checkbox.
        We also need to update the selected state of the associated palette and slot
        and the sprite preview so checking the box of an edit slow on dialog load shows a sprite.
        """
        index = select_combo.currentIndex()

        character = self.ui.character_select.currentData()
        sprite_cache = self.paths.get_sprite_cache(character)

        is_checked = (check_state == QtCore.Qt.CheckState.Checked)
        select_combo.setItemData(index, is_checked, ROLE_CHECK_STATE)

        slot_type = select_combo.itemData(index, ROLE_SLOT_TYPE)
        select_name = select_combo.itemText(index)

        self._mark_palette_selected(character, palette_id, select_name, slot_type, is_checked)
        self._update_sprite_preview(sprite_cache, character, palette_id, select_name)

    def update_sprite_preview(self, palette_id, select_check, select_combo):
        """
        A character or palette selection was made and we need to update the UI.
        Note that if a palette selection of "No Palette" was made that we
        clear the graphics view and do not insert another image into it.
        """
        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

        select_name = select_combo.currentText()
        slot_type = select_combo.currentData(ROLE_SLOT_TYPE)
        is_checked = select_combo.currentData(ROLE_CHECK_STATE)

        if self.allow_multi_select:
            can_check = (slot_type != PALETTE_NONE)
            select_check.setEnabled(can_check)
            check_state = QtCore.Qt.CheckState.Unchecked

            if can_check:
                check_state = QtCore.Qt.CheckState.Checked if is_checked else QtCore.Qt.CheckState.Unchecked

            select_check.setCheckState(check_state)

        character = self.ui.character_select.currentData()
        sprite_cache = self.paths.get_sprite_cache(character)

        # If there are no cached sprites we can't show a preview to the user.
        if not sprite_cache:
            character_name = self.ui.character_select.currentText()
            message = f"No Sprites for {character_name} have been extracted or edited!"
            self.parent().show_message_dialog("No Preview Available", message)
            return

        self._mark_palette_selected(character, palette_id, select_name, slot_type, is_checked)

        # Only update the preview with a new image if we did not pick the "No Palette" slot.
        if slot_type != PALETTE_NONE:
            self._update_sprite_preview(sprite_cache, character, palette_id, select_name)

    def get_selected_palettes(self):
        """
        Helper method to create a dict of files to apply to the game that we can pass to ApplyThread.
        """
        selected_palettes = defaultdict(lambda: defaultdict(dict))

        for character, palette_id, select_name in self.selected_palettes:
            if select_name == SLOT_NAME_EDIT:
                hpl_files = self.paths.get_edit_palette(character, palette_id)
            else:
                hpl_files = self.paths.get_saved_palette(character, palette_id, select_name)

            selected_palettes[character][palette_id][select_name] = hpl_files

        if not self.allow_multi_select:
            for character, palette_id, select_name in self.selected_palettes:
                if len(selected_palettes[character][palette_id]) > 1:
                    raise AppError("Invalid Palette Selection!", "Cannot select multiple slots per palette!")

        return selected_palettes
