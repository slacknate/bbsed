import io
import os
import re
import hashlib

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import HIPImage
from libhpl import PNGPaletteImage

from .ui.select_dialog_ui import Ui_Dialog

from .char_info import PALETTE_FMT, VALID_CHARACTERS
from .exceptions import AppError
from .util import *

ROLE_CHECK_STATE = QtCore.Qt.ItemDataRole.UserRole

PALETTE_GROUP_PREFIX = "palette_{}"
SELECT_COMBOBOX_PREFIX = "select_{}"
SELECT_CHECK_PREFIX = "check_{}"

SELECTION_DELIMITER = ";"
DATA_DELIMITER = ","


def generate_selection_hash(hpl_files_list):
    """
    Generate a SHA-256 hash of the contents of the given HPL files.
    This is used to determine if a selection has changed on dialog accept so we know
    which palettes need be applied to the game files.
    """
    palette_contents = b""

    for hpl_full_path in hpl_files_list:
        with open(hpl_full_path, "rb") as hpl_fp:
            palette_contents += hpl_fp.read()

    return hashlib.sha256(palette_contents).hexdigest()


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

    def __init__(self, paths, multi_select, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.paths = paths

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

    def _get_hpl_files(self, character, palette_id, palette_num, slot_name):
        """
        Get the HPL files for this character/palette/slot selection.
        We prefer palette files from the edit path so unsaved changes may be applied.
        If there are no active edits for a given file it will be retrieved from the save path.
        """
        # Lambda-11 palette files use the Nu-13 character prefix.
        hpl_char = character
        if character == "rm":
            hpl_char = "ny"

        hpl_files = []
        hpl_file_names = [PALETTE_FMT.format(hpl_char).format(palette_num, i) for i in range(FILES_PER_PALETTE)]

        edit_path = self.paths.get_edit_palette_path(character, palette_id, slot_name)
        edit_files_list = self.paths.get_edit_palette(character, palette_id, slot_name)
        edit_file_names = [os.path.basename(hpl_path) for hpl_path in edit_files_list]

        save_path = self.paths.get_palette_save_path(character, palette_id, slot_name)

        for hpl_file_name in hpl_file_names:
            if hpl_file_name in edit_file_names:
                hpl_files.append(os.path.join(edit_path, hpl_file_name))

            else:
                hpl_files.append(os.path.join(save_path, hpl_file_name))

        return hpl_files

    def _get_selected(self, character, palette_id, slot_name):
        """
        Get the "is selected" status of the given character/palette/slot choice.
        Use for implementing custom behavior in subclasses.
        """
        raise NotImplementedError

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
            for palette_id, palette_num in iter_palettes():
                character_saves = self.paths.get_palette_saves(character, palette_id)

                for slot_name in character_saves:
                    is_selected = self._get_selected(character, palette_id, slot_name)

                    if is_selected:
                        hpl_files = self._get_hpl_files(character, palette_id, palette_num, slot_name)
                        selected_palettes[character][palette_id][slot_name] = hpl_files

        if not self.multi_select:
            for select_info in iter_selection(selected_palettes):
                if len(select_info) > 1:
                    raise AppError("Invalid Palette Selection!", "Cannot select multiple slots per palette!")

        return selected_palettes

    def accept(self):
        QtWidgets.QDialog.accept(self)

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

    def select_character(self):
        """
        A character was selected.
        We populate the palette selection widgets to reflect selections that were previously
        made and applied to the game for this character, as well as any saved palettes and current edits.
        """
        if not self.ui.palette_select.isEnabled():
            self.ui.palette_select.setEnabled(True)

        with block_signals(self.ui.palette_select):
            self.ui.palette_select.setCurrentIndex(0)

        self.select_palette()

    def _select_palette(self, character, palette_id):
        """
        A palette has been chosen by the user.
        Use for implementing custom behavior in subclasses.
        """
        raise NotImplementedError

    def select_palette(self):
        """
        A palette was selected.
        Reload the save slots. In single-select mode we set the slot to the configured selection.
        """
        if not self.ui.slot_select.isEnabled():
            self.ui.slot_select.setEnabled(True)

        with block_signals(self.ui.slot_select):
            self._update_save_slots()

        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()

        self._select_palette(character, palette_id)

        self.select_slot()

    def _select_slot(self, character, palette_id, slot_name):
        """
        A slot has been chosen by the user.
        Use for implementing custom behavior in subclasses.
        """
        raise NotImplementedError

    def select_slot(self):
        """
        A slot has been selected.
        Update the configuration value and the palette displayed in the sprite preview.
        """
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_name = self.ui.slot_select.currentText()

        self._select_slot(character, palette_id, slot_name)
        self._refresh()

    def _refresh(self):
        """
        Refresh the sprite preview of the current selection.
        """
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_name = self.ui.slot_select.currentText()

        self._update_sprite_preview(character, palette_id, slot_name)

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


class ApplyDialog(SelectDialog):
    """
    A dialog for selecting color palettes to apply to the BBCF game files.
    """
    def __init__(self, paths, config, parent=None):
        SelectDialog.__init__(self, paths, False, parent=parent)
        self.config = config
        self.initial = config.copy()

    def _remove_unchanged(self, selected_palettes):
        """
        Filter out any palette selections that have not changed since dialog creation.
        This allows for applying palettes to the game files to have as short a duration as possible.
        """
        for character, palette_info in list(selected_palettes.items()):
            remove_list = []

            for palette_id, select_info in palette_info.items():
                for select_name, hpl_files_list in select_info.items():
                    files_hash = generate_selection_hash(hpl_files_list)
                    initial_name, initial_hash = self._get_initial_selection(character, palette_id)

                    # If the selection name does not match the initial selection or the
                    # current palette hash does not match the initial hash, then this selection
                    # has changed and we should not remove it from our selections.
                    should_remove = (select_name == initial_name and files_hash == initial_hash)
                    remove_list.append(should_remove)

                    # If our hash has changed but the initial and config values for this
                    # character/palette are a match, then the user has made some edits and
                    # accepted the palette dialog without making selection changes. We need
                    # to handle that scenario and ensure we update the files hash that is
                    # present in the config so the config data accurately reflects selections.
                    initial_eq_config = self._initial_eq_config(character, palette_id)
                    if files_hash != initial_hash and initial_eq_config:
                        self._select_slot(character, palette_id, select_name, files_hash)

            if all(remove_list):
                selected_palettes.pop(character)

    def _get_selection(self):
        """
        This dialog has a file saved config. This means we can look for changes
        since the previous time palettes were applied and only apply character
        palettes that have changed. This reduces the time it takes to apply palettes.
        """
        selection = SelectDialog._get_selection(self)
        self._remove_unchanged(selection)
        return selection

    @staticmethod
    def _parse_selection(selection):
        """
        In previous versions of BBSED, the apply config did not include a hash.
        We should be able to handle both config value styles.
        """
        try:
            select_name, select_hash = selection.split(DATA_DELIMITER)

        # Handle the old-style config values.
        except ValueError:
            select_name = selection
            select_hash = ""

        return select_name, select_hash

    def _get_initial_selection(self, character, palette_id):
        """
        Get the selection state of the given character/palette from the previous palette apply.
        """
        selection = self.initial[character][palette_id]
        return self._parse_selection(selection)

    def _initial_eq_config(self, character, palette_id):
        """
        Check if the initial and config values for the given character/palette_id are equal.
        """
        return self.initial[character][palette_id] == self.config[character][palette_id]

    def _get_selected(self, character, palette_id, slot_name):
        """
        Check if the given slot is the config-selected slot.
        """
        selection = self.config[character][palette_id]
        select_name, _ = self._parse_selection(selection)
        return select_name == slot_name

    def _select_palette(self, character, palette_id):
        """
        Set the current slot selection from the config data.
        """
        selection = self.config[character][palette_id]
        slot_name, _ = self._parse_selection(selection)

        index = self.ui.slot_select.findText(slot_name)
        with block_signals(self.ui.slot_select):
            self.ui.slot_select.setCurrentIndex(index)

    def _select_slot(self, character, palette_id, slot_name, select_hash=None):
        """
        Set the given character/palette/slot as selected, optionally providing a hash.
        If no has is provided then we generate one here.
        """
        if select_hash is None:
            palette_num = palette_id_to_number(palette_id)
            hpl_files_list = self._get_hpl_files(character, palette_id, palette_num, slot_name)
            select_hash = generate_selection_hash(hpl_files_list)

        self.config[character][palette_id] = slot_name + DATA_DELIMITER + select_hash


class ExportDialog(SelectDialog):
    """
    A dialog for selecting palettes to export.
    """
    def __init__(self, paths, parent=None):
        SelectDialog.__init__(self, paths, True, parent=parent)
        self.ui.ms_checkbox.stateChanged.connect(self.multi_select_slot)
        self.config = defaultdict(lambda: defaultdict(str))

    def _get_slot_multi_selected(self, character, palette_id, slot_name):
        """
        Get the `is_selected` status of the given character/palette/slot selection as a boolean.
        """
        selections_raw = self.config[character][palette_id]
        is_selected = False

        match = re.search(r";?(" + slot_name + r",[01]);?", selections_raw)
        if match is not None:
            _, is_selected_raw = match.group(1).split(",")
            is_selected = bool(int(is_selected_raw))

        return is_selected

    def _set_slot_multi_selected(self, character, palette_id, slot_name, is_selected):
        """
        Set the `is_selected` status of the given character/palette/slot selection in the config.
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

        check_state = QtCore.Qt.CheckState.Checked if is_selected else QtCore.Qt.CheckState.Unchecked
        with block_signals(self.ui.ms_checkbox):
            self.ui.ms_checkbox.setCheckState(check_state)

    def _get_selected(self, character, palette_id, slot_name):
        """
        Get the "is selected" status of the given character/palette/slot choice.
        """
        return self._get_slot_multi_selected(character, palette_id, slot_name)

    def _select_palette(self, character, palette_id):
        """
        This dialog does not require an implementation for this method.
        The `_select_slot` implementation handles what we would need to do here.
        """

    def _select_slot(self, character, palette_id, slot_name):
        """
        A slot has been selected.
        Ensure the checkbox has been enabled and if it has
        not yet already been enabled we should do so now.
        Update the checkbox state from the selection state of this character/palette/slot.
        """
        if not self.ui.ms_checkbox.isEnabled():
            self.ui.ms_checkbox.setEnabled(True)

        is_selected = self._get_slot_multi_selected(character, palette_id, slot_name)
        self._set_slot_multi_selected(character, palette_id, slot_name, is_selected)

    def multi_select_slot(self, check_state):
        """
        The checkbox state has changed.
        Update the select state of the current character/palette/slot choice.
        """
        character = self.ui.character_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_name = self.ui.slot_select.currentText()

        is_selected = (check_state == QtCore.Qt.CheckState.Checked)

        self._set_slot_multi_selected(character, palette_id, slot_name, is_selected)
