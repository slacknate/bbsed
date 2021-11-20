import io
import os

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import HIPImage
from libhpl import PNGPaletteImage

from .ui.select_dialog_ui import Ui_Dialog

from .exceptions import AppError
from .char_info import CHARACTER_INFO
from .util import *

ROLE_CHECK_STATE = QtCore.Qt.ItemDataRole.UserRole

PALETTE_GROUP_PREFIX = "palette_{}"
SELECT_COMBOBOX_PREFIX = "select_{}"
SELECT_CHECK_PREFIX = "check_{}"


class SelectDialog(QtWidgets.QDialog):

    selection_made = QtCore.pyqtSignal(QtWidgets.QDialog)

    def __init__(self, paths, config=None, multi_select=False, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.paths = paths
        self.config = config
        self.multi_select = multi_select

        self.selected = set()
        self.unselected = set()

        self.setWindowTitle("Select Palettes")

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        self.current_sprite = io.BytesIO()
        self.sprite = PNGPaletteImage()

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

        def _update_multislot_callback(_palette_id, _select_check, _select_combo):
            """
            Create a callback to update the check state of the multi-select checkbox.
            """
            return lambda _check_state: self.update_check_state(_palette_id, _check_state, _select_check, _select_combo)

        def _select_palette_callback(_palette_id, _select_check, _select_combo):
            """
            Create a callback to update the sprite preview that works with any Qt signal.
            """
            return lambda *_, **__: self.select_palette(_palette_id, _select_check, _select_combo)

        def _show_sprite_callback(_palette_id, _select_check, _select_combo):
            """
            Create a callback to update the check state of the multi-select checkbox.
            """
            return lambda *_, **__: self.show_sprite(_palette_id, _select_check, _select_combo)

        for palette_id, palette_group, select_check, select_combo in self.iter_widgets():
            # If we allow for selecting multiple palettes per slot we need to set up a
            # signal to update the state of the checkbox for each combobox item.
            if self.multi_select:
                select_check.stateChanged.connect(_update_multislot_callback(palette_id, select_check, select_combo))
            # Otherwise hide the checkbox and don't worry about signals.
            else:
                select_check.hide()

            # We want combo box selections to update the sprite preview.
            select_combo.currentIndexChanged.connect(_select_palette_callback(palette_id, select_check, select_combo))

            # We also want to be able to easily change palette preview by clicking a palette group box.
            palette_group.mousePressEvent = _show_sprite_callback(palette_id, select_check, select_combo)

        if self.config is not None:
            self._load_config()

    def _load_config(self):
        """
        Set the initial state of the dialog from the saved config.
        This will only occur if the config exists.
        """
        for character, palette_id, config_value in self.config:
            _, select_check, select_combo = self._get_widgets(palette_id)

            # We block signals for these widgets so that we do not trigger any callbacks when setting the initial
            # dialog state. We currently have no character selected and no palette slots added and as such if we
            # trigger a callback here we will definitely encounter an error condition.
            with block_signals(select_check, select_combo):
                # If we are in multi-select mode we need to parse this value to retrieve all selections
                # for this character/palette ID.
                if self.multi_select:
                    for selection in config_value.split(";"):
                        select_name, is_selected = selection.split(",")
                        is_selected = bool(int(is_selected))

                        self._mark_palette_selected(character, palette_id, select_name, select_check, is_selected)

                # If we aren't in multi-select mode then we only have one selection for this character/palette ID.
                else:
                    self._mark_palette_selected(character, palette_id, config_value, select_check, True)

    def _get_config_value(self, character, palette_id, select_name, is_selected):
        """
        Get the value we need to store in our backend config based on the dialog mode
        and our current selection.
        """
        # If we are in multi-select mode then our config value contains multiple selections
        # which are (select_name, is_selected) tuples.
        if self.multi_select:
            existing_value = self.config[character][palette_id]
            select_value = f"{select_name},{int(is_selected)}"

            # If this select name has previously been selected then we need to find where it exists in
            # the config value for this character/palette ID combo and update that value in place.
            if select_name in existing_value:
                start = existing_value.find(select_name)
                end = start + len(select_name) + 2
                config_value = existing_value[:start] + select_value + existing_value[end:]

            # If other selections have been made we need to append to the selection config.
            elif existing_value:
                config_value = ";" + select_value

            # If no selections have been made then this is our only current selection.
            else:
                config_value = select_value

        # Otherwise our config value is simply the selection name.
        else:
            config_value = select_name

        return config_value

    def _save_config(self):
        """
        Update our config with the most recent selections and save them to disk.
        """
        for character, palette_id, select_name in self.selected:
            config_value = self._get_config_value(character, palette_id, select_name, True)
            self.config[character][palette_id] = config_value

        # We only have to worry about unselected palettes for multi-select mode.
        # For single-select mode, the config value is just a singular value of the selected palette.
        if self.multi_select:
            for character, palette_id, select_name in self.unselected:
                config_value = self._get_config_value(character, palette_id, select_name, False)
                self.config[character][palette_id] = config_value

        self.config.save()

    def accept(self):
        QtWidgets.QDialog.accept(self)

        # Only update a backend config for this dialog if it exists.
        if self.config is not None:
            self._save_config()

        self.selection_made.emit(self)

    def _get_widgets(self, palette_id):
        """
        The attribute names of these widgets are explicitly defined in Qt Designer.
        These attributes will in fact exist and we get at them this way to avoid writing a giant block of
        code that would manually call out these widgets `GAME_MAX_PALETTES` times.
        """
        palette_group = getattr(self.ui, PALETTE_GROUP_PREFIX.format(palette_id))
        select_check = getattr(self.ui, SELECT_CHECK_PREFIX.format(palette_id))
        select_combo = getattr(self.ui, SELECT_COMBOBOX_PREFIX.format(palette_id))
        return palette_group, select_check, select_combo

    def iter_widgets(self):
        """
        Helper to iterate our palette selection widgets.
        """
        for palette_id, _ in iter_palettes():
            palette_group, select_check, select_combo = self._get_widgets(palette_id)
            yield palette_id, palette_group, select_check, select_combo

    def _update_ui_for_selected(self, character_saves, character, palette_id, select_check, select_combo):
        """
        Read our current selections and update the UI to reflect selection choices for this character/palette ID.
        We set the combobox to the item with the smallest index that is also selected. We also update the checkbox
        check state accordingly.
        """
        first_index = None
        first_selected = False

        selections = []

        for select_name in character_saves:
            is_selected = ((character, palette_id, select_name) in self.selected)

            # In multi-select mode we do not want to select any of the game slots.
            if self.multi_select and select_name not in GAME_SLOT_NAMES:
                selections.append((select_name, is_selected))

            # In single-select mode we are looking for the one selection for this character and palette ID.
            elif is_selected:
                selections.append((select_name, True))

        for select_name, is_selected in selections:
            index = select_combo.findText(select_name)
            select_combo.setItemData(index, is_selected, ROLE_CHECK_STATE)

            if is_selected and (first_index is None or index < first_index):
                first_selected = is_selected
                first_index = index

        # We need to use a value index. Just default to the first item in the combobox.
        if first_index is None:
            first_index = 0

        check_state = QtCore.Qt.CheckState.Checked if first_selected else QtCore.Qt.CheckState.Unchecked

        with block_signals(select_check, select_combo):
            select_check.setCheckState(check_state)
            select_combo.setCurrentIndex(first_index)

    def select_character(self):
        """
        A character was selected.
        We populate the palette selection widgets to reflect selections that were previously
        made and applied to the game for this character, as well as any saved palettes and current edits.
        """
        if not self.ui.palette_pages.isEnabled():
            self.ui.palette_pages.setEnabled(True)

        character = self.ui.character_select.currentData()

        for palette_id, _, select_check, select_combo in self.iter_widgets():
            with block_signals(select_combo):
                # Clear the combo box before re-populating it.
                select_combo.clear()

                # Allow the user to choose not to change this palette in game.
                # Note that if we are in multi-select mode we do not add this slot.
                # In multi-select mode the game-slot equivalent is not setting the check for any slots.
                if not self.multi_select:
                    # TODO: BBTAG, BBCP, BBCS, BBCT
                    select_combo.addItem(SLOT_NAME_BBCF, PALETTE_BBCF)
                    select_combo.setItemData(0, False, ROLE_CHECK_STATE)

                # Show any saved palettes that map to this palette ID.
                character_saves = self.paths.get_palette_saves(character, palette_id)
                for save_name in character_saves:
                    if save_name not in GAME_SLOT_NAMES:
                        select_combo.addItem(save_name, PALETTE_SAVE)
                        index = select_combo.findText(save_name)
                        select_combo.setItemData(index, False, ROLE_CHECK_STATE)

                # If there are no added palette saves we should disable these widgets as they
                # have nothing for the user to interact with and we also want to prevent errors from occurring.
                if select_combo.count() < 1:
                    select_check.setEnabled(False)
                    select_combo.setEnabled(False)

                # Update the UI to reflect the current selections for this character and palette ID.
                self._update_ui_for_selected(character_saves, character, palette_id, select_check, select_combo)

    def show_sprite(self, palette_id, _, select_combo):
        """
        Callback for clicking on a selection groupbox.
        This does nothing except update the sprite preview.
        This update only occurs if the clicked group contains a coombo
        box with a valid palette selection.
        """
        select_name = select_combo.currentText()

        # Only update the preview if we have a valid selection.
        if select_name:
            character = self.ui.character_select.currentData()
            self._update_sprite_preview(character, palette_id, select_name)

    def _update_sprite_preview(self, character, palette_id, select_name):
        """
        A character selection or palette selection was made and
        we need to update the UI to show the most relevant preview.
        """
        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

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

    def _mark_palette_selected(self, character, palette_id, select_name, select_check, is_selected):
        """
        Update our selections that will be saved to disk in the apply config as well as
        the selections data we use to generate the data to apply to game files.
        Note that if the dialog is not accepted these datas are discarded.
        """
        select_key = (character, palette_id, select_name)

        if is_selected:
            self.selected.add(select_key)
            self.unselected.discard(select_key)

        else:
            self.selected.discard(select_key)
            self.unselected.add(select_key)

        # Update the state of the associated check box. If we are not in multi-select mode this widget is hidden
        # but we always set it for the sake of ease of implementation.
        check_state = QtCore.Qt.CheckState.Checked if is_selected else QtCore.Qt.CheckState.Unchecked
        select_check.setCheckState(check_state)

    def update_check_state(self, palette_id, check_state, select_check, select_combo):
        """
        Update the state of our multi-select checkbox.
        We also need to update the selected state of the associated palette and slot
        and the sprite preview so checking the box of an edit slow on dialog load shows a sprite.
        """
        index = select_combo.currentIndex()
        character = self.ui.character_select.currentData()

        is_selected = (check_state == QtCore.Qt.CheckState.Checked)
        select_combo.setItemData(index, is_selected, ROLE_CHECK_STATE)
        select_name = select_combo.itemText(index)

        with block_signals(select_check, select_combo):
            self._mark_palette_selected(character, palette_id, select_name, select_check, is_selected)

        self._update_sprite_preview(character, palette_id, select_name)

    def _deselect_previous(self, character, palette_id, select_combo):
        """
        Helper to find any previously selected palette with the given character and palette ID
        and remove it from the current selections.
        """
        for _character, _palette_id, select_name in self.selected:
            if _character == character and _palette_id == palette_id:
                select_key = (character, palette_id, select_name)

                index = select_combo.findText(select_name)
                select_combo.setItemData(index, False, ROLE_CHECK_STATE)

                self.selected.discard(select_key)
                self.unselected.add(select_key)

                break

    def select_palette(self, palette_id, select_check, select_combo):
        """
        A character or palette selection was made and we need to update the UI.
        """
        character = self.ui.character_select.currentData()
        select_name = select_combo.currentText()
        index = select_combo.currentIndex()

        if self.multi_select:
            is_selected = select_combo.currentData(ROLE_CHECK_STATE)

        # In single-select mode we need to de-select the previous palette selection before
        # adding the new palette so we do not end up with more than one selection for a given character and palette ID.
        else:
            self._deselect_previous(character, palette_id, select_combo)
            select_combo.setItemData(index, True, ROLE_CHECK_STATE)
            is_selected = True

        with block_signals(select_check, select_combo):
            self._mark_palette_selected(character, palette_id, select_name, select_check, is_selected)

        self._update_sprite_preview(character, palette_id, select_name)

    def get_selected_palettes(self):
        """
        Helper method to create a dict of files to apply to the game that we can pass to ApplyThread.
        """
        selected_palettes = defaultdict(lambda: defaultdict(dict))

        for character, palette_id, select_name in self.selected:
            hpl_files = self.paths.get_saved_palette(character, palette_id, select_name)
            selected_palettes[character][palette_id][select_name] = hpl_files

        if not self.multi_select:
            for character, palette_id, select_name in self.selected:
                if len(selected_palettes[character][palette_id]) > 1:
                    raise AppError("Invalid Palette Selection!", "Cannot select multiple slots per palette!")

        return selected_palettes
