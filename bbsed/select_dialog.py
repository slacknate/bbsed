import io
import os
import re

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import HIPImage
from libhpl import PNGPaletteImage

from .ui.select_dialog_ui import Ui_Dialog

from .char_info import VALID_CHARACTERS
from .exceptions import AppError
from .util import *

ROLE_CHECK_STATE = QtCore.Qt.ItemDataRole.UserRole

PALETTE_GROUP_PREFIX = "palette_{}"
SELECT_COMBOBOX_PREFIX = "select_{}"
SELECT_CHECK_PREFIX = "check_{}"


def iter_selection(selected_palettes):
    """
    Iterate selected palettes and yield the selection info.
    Used to verify that when we are in single-select that we have not
    somehow managed to make multiple selections.
    """
    for character, palette_info in selected_palettes.items():
        for palette_id, select_info in palette_info.items():
            yield select_info


class SelectDialog(QtWidgets.QDialog):

    selection_made = QtCore.pyqtSignal(dict)

    def __init__(self, paths, config, diff_config=None, multi_select=False, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.paths = paths
        self.config = config
        self.diff_config = diff_config
        self.initial = None

        self.selected = set()
        self.unselected = set()
        self.multi_select = multi_select
        self.ui.ms_checkbox.setVisible(multi_select)

        self.setWindowTitle("Select Palettes")

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        self.current_sprite = io.BytesIO()
        self.sprite = PNGPaletteImage()

        self.ui.character_select.currentIndexChanged.connect(self.select_character)
        with block_signals(self.ui.character_select):
            for _, (character_name, character) in iter_characters():
                self.ui.character_select.addItem(character_name, character)

            self.ui.character_select.setCurrentIndex(-1)

        self.ui.palette_select.currentIndexChanged.connect(self.select_palette)
        with block_signals(self.ui.palette_select):
            for palette_id, palette_num in iter_palettes():
                self.ui.palette_select.addItem(palette_id, palette_num)

            self.ui.palette_select.setCurrentIndex(-1)

        self.ui.slot_select.currentIndexChanged.connect(self.select_slot)
        self.ui.ms_checkbox.stateChanged.connect(self.multi_select_slot)

        self.initial = self.config.copy()

    def _remove_unchanged(self, selected_palettes):
        """
        Filter out any palette selections that have not changed since dialog creation.
        This allows for applying palettes to the game files to have as short a duration as possible.
        """
        for character, palette_info in list(selected_palettes.items()):
            remove_list = []

            for palette_id, _ in palette_info.items():
                initial_name = self.initial[character][palette_id]
                current_name = self.config[character][palette_id]

                # If there is no diff config then there is not a diff to be had.
                diff_name = self.diff_config[character][palette_id]

                # Check if the selection has changed.
                same_selection = (initial_name == current_name)
                # Check if the diff config does not match the selection.
                no_diff = (diff_name == current_name)

                should_remove = same_selection and no_diff
                remove_list.append(should_remove)

            if all(remove_list):
                selected_palettes.pop(character)

    def _get_selection(self):
        """
        Get the current selected palettes.

        If this selection is config saved then we check the diff between the configuration as it existed at dialog
        creation vs as it currently exists after a selection has been made. We do this to save time during the
        procedures to export or apply palettes.

        Otherwise we just get the current selection as directly reflected by the state of the config.
        """
        selected_palettes = defaultdict(lambda: defaultdict(dict))

        for character in VALID_CHARACTERS:
            for palette_id, _ in iter_palettes():
                character_saves = self.paths.get_palette_saves(character, palette_id)

                for slot_name in character_saves:
                    if self.multi_select:
                        is_selected = self._get_slot_multi_select(character, palette_id, slot_name)

                    else:
                        is_selected = (self.config[character][palette_id] == slot_name)

                    if is_selected:
                        hpl_files = self.paths.get_saved_palette(character, palette_id, slot_name)
                        selected_palettes[character][palette_id][slot_name] = hpl_files

        if self.diff_config is not None:
            self._remove_unchanged(selected_palettes)

        if not self.multi_select:
            for select_info in iter_selection(selected_palettes):
                if len(select_info) > 1:
                    raise AppError("Invalid Palette Selection!", "Cannot select multiple slots per palette!")

        return selected_palettes

    def accept(self):
        QtWidgets.QDialog.accept(self)

        self.config.save()

        selection = self._get_selection()
        self.selection_made.emit(selection)

    def _update_save_slots(self):
        """
        We have selected a character or a palette.
        We need to update the available slots presented in the UI.
        """
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        character_saves = self.paths.get_palette_saves(character, palette_id)

        self.ui.slot_select.clear()

        # TODO: BBTAG, BBCP, BBCS, BBCT
        # In multi-select mode we do not want to select any of the game slots.
        # This prevents exporting of the palettes that come with the game.
        if not self.multi_select:
            self.ui.slot_select.addItem(SLOT_NAME_BBCF, PALETTE_BBCF)

        for save_name in character_saves:
            if save_name not in GAME_SLOT_NAMES:
                self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

        # Set the selected slot to the BBCF game slot.
        self.ui.slot_select.setCurrentIndex(0)

    def _refresh(self):
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_name = self.ui.slot_select.currentText()

        self._update_sprite_preview(character, palette_id, slot_name)

    def select_character(self):
        """
        A character was selected.
        We populate the palette selection widgets to reflect selections that were previously
        made and applied to the game for this character, as well as any saved palettes and current edits.
        """
        with block_signals(self.ui.palette_select):
            self.ui.palette_select.setCurrentIndex(0)

        self.select_palette()

    def select_palette(self):
        """
        A palette was selected.
        Reload the save slots. In single-select mode we set the slot to the configured selection.
        """
        with block_signals(self.ui.slot_select):
            self._update_save_slots()

        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()

        if self.multi_select:
            selections_raw = self.config[character][palette_id]
            selections_split1 = [selection for selection in selections_raw.split(";") if selection != ""]

            selections_split2 = []
            for selection in selections_split1:
                selection_split = selection.split(",")
                if selection_split:
                    selections_split2.append(selection_split)

            selections = [(slot_name, bool(int(is_selected))) for slot_name, is_selected in selections_split2]
            selections.sort(key=lambda _item: _item[0])

        else:
            slot_name = self.config[character][palette_id]
            index = self.ui.slot_select.findText(slot_name)

            with block_signals(self.ui.slot_select):
                self.ui.slot_select.setCurrentIndex(index)

        self.select_slot()

    def select_slot(self):
        """
        A slot has been selected.
        Update the configuration value and the palette displayed in the sprite preview.
        """
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_name = self.ui.slot_select.currentText()

        # Set the selection in the config.
        if self.multi_select:
            # This checkbox is disabled by default.
            # If it is still disabled here we need to enable it so the user can interact with it.
            # This check is made here because the checkbox needs to stay disabled until a character is
            # selected so the user cannot interact with it without a valid character/palette/slot combo.
            if not self.ui.ms_checkbox.isEnabled():
                self.ui.ms_checkbox.setEnabled(True)

            is_selected = self._get_slot_multi_select(character, palette_id, slot_name)
            check_state = QtCore.Qt.CheckState.Checked if is_selected else QtCore.Qt.CheckState.Unchecked
            self.multi_select_slot(check_state)

        else:
            self.config[character][palette_id] = slot_name
            self._refresh()

    def _get_slot_multi_select(self, character, palette_id, slot_name):
        """
        Get the `is_selected` status of the given character/palette/slot combo as a boolean.
        """
        selections_raw = self.config[character][palette_id]
        is_selected = False

        match = re.search(r";?(" + slot_name + r",[01]);?", selections_raw)
        if match is not None:
            _, is_selected_raw = match.group(1).split(",")
            is_selected = bool(int(is_selected_raw))

        return is_selected

    def _set_slot_multi_select(self, character, palette_id, slot_name, is_selected):
        """
        Set the `is_selected` status of the given character/palette/slot combo in the config.
        """
        selections_raw = self.config[character][palette_id]

        old_config_value = f"{slot_name},{int(not is_selected)}"
        new_config_value = f"{slot_name},{int(is_selected)}"

        # If this slot has been selected before then we can just do a good ol' string replace to update the value.
        if old_config_value in selections_raw:
            selections_raw = selections_raw.replace(old_config_value, new_config_value)

        # Otherwise we need to append this selection to the existing ones.
        elif slot_name not in selections_raw:
            # If no selections have yet been made at all then we need to skip the delimiter.
            if selections_raw:
                selections_raw += ";"

            selections_raw += new_config_value

        self.config[character][palette_id] = selections_raw

    def multi_select_slot(self, check_state):
        """
        A slot has been selected (specifically applies in multi-select mode).
        This is the callback for the multi-select checkbox state changing.
        Update the configuration value and the palette displayed in the sprite preview.
        """
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_name = self.ui.slot_select.currentText()
        is_selected = bool(check_state)

        self._set_slot_multi_select(character, palette_id, slot_name, is_selected)
        with block_signals(self.ui.ms_checkbox):
            self.ui.ms_checkbox.setCheckState(check_state)

        self._refresh()

    def _update_sprite_preview(self, character, palette_id, select_name):
        """
        A character selection or palette selection was made and
        we need to update the UI to show the most relevant preview.
        """
        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

        # If there is not a valid slot selection then we cannot update the preview.
        # There is not a palette to load from the save path.
        if not select_name:
            return

        # Get the cached sprites for this character.
        sprite_cache = self.paths.get_sprite_cache(character)
        hip_full_path = None

        # Get the first sprite from our cache that is an image of to show as a preview the selected character.
        # We don't really need to provide preview options here as this is a quick preview.
        # We look for the first file starting with the selected character prefix because some extracted character data
        # contains sprites for other characters. I assume this is for special intros and such.
        for _hip_full_path in sprite_cache:
            _hip_file = os.path.basename(_hip_full_path)

            if _hip_file.startswith(character):
                hip_full_path = _hip_full_path
                break

        # If there are no cached sprites we can't show a preview to the user.
        if hip_full_path is None:
            character_name = self.ui.character_select.currentText()
            message = f"No Sprites for {character_name} have been extracted or edited!"
            self.parent().show_message_dialog("No Preview Available", message)
            return

        try:
            hip_image = HIPImage()
            hip_image.load_hip(hip_full_path)

            sprite_data = io.BytesIO()
            hip_image.save_png(sprite_data)

        except Exception:
            hip_file = os.path.basename(hip_full_path)
            self.parent().show_error_dialog("Error Converting Sprite", f"Failed to convert {hip_file} to PNG image!")
            return

        try:
            self.sprite.load_png(sprite_data)

        except Exception:
            self.parent().show_error_dialog("Error Loading Sprite", f"Failed to load converted PNG sprite!")
            return

        hpl_files = self.paths.get_saved_palette(character, palette_id, select_name)

        # The first sprite is always associated to the first palette file as far as I can tell.
        # We can make this assumption until it is proven wrong.
        palette_full_path = hpl_files[0]
        updated_sprite = io.BytesIO()

        try:
            self.sprite.load_hpl(palette_full_path)
            self.sprite.save_png(updated_sprite)

        except Exception:
            message = f"Failed to replace the palette of the current sprite!"
            self.parent().show_error_dialog("Error Updating Palette", message)
            return

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(updated_sprite.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        self.sprite_scene.addPixmap(png_pixmap)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()
