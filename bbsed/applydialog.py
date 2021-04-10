import io
import os

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import replace_palette

from .ui.applydialog_ui import Ui_Dialog

from .char_info import CHARACTER_INFO, VALID_CHARACTERS
from .config import Configuration
from .util import *

PALETTE_GROUP_PREFIX = "palette_{}"
SELECT_COMBOBOX_PREFIX = "select_{}"

SLOT_NAME_INITIAL = ""
SLOT_NAME_NONE = "None"
PALETTE_NONE = 0


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


def generate_apply_settings():
    """
    Generate the settings definition of ApplyConfig
    programmatically to save codespace.
    """
    settings = {}

    for character in VALID_CHARACTERS:
        settings[character] = {}

        for palette_number in range(GAME_MAX_PALETTES):
            palette_id = palette_number_to_id(palette_number)

            settings[character][palette_id] = SLOT_NAME_INITIAL

    return settings


class ApplyConfig(Configuration):

    SETTINGS = generate_apply_settings()

    def __init__(self, cfg_path):
        Configuration.__init__(self, cfg_path)


class ApplyDialog(QtWidgets.QDialog):
    def __init__(self, paths, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.paths = paths
        self.config = ApplyConfig(paths.apply_config_file)
        self.selected_palettes = {}
        self.updated = {}

        self.setWindowTitle("Apply Palettes To BBCF")

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
            for _, (character_name, character_abbr) in sorted_chars:
                self.ui.character_select.addItem(character_name, character_abbr)

            self.ui.character_select.currentIndexChanged.connect(self.select_character)
            self.ui.character_select.setCurrentIndex(-1)

        def _update_preview_callback(_palette_id, _select_combo):
            """
            Create a callback to update the sprite preview that works with any Qt signal.
            """
            return lambda *_, **__: self.update_sprite_preview(_palette_id, _select_combo)

        # Set up palette selection.
        for palette_id, palette_group, select_combo in self.iter_widgets():
            callback = _update_preview_callback(palette_id, select_combo)
            # We want combo box selections to update the sprite preview.
            select_combo.currentIndexChanged.connect(callback)
            # We also want to be able to easily change palette preview by clicking a palette group box.
            palette_group.mousePressEvent = callback

    def accept(self):
        message = "Do you wish to apply the selected palettes to the BBCF game files?"
        apply = self.parent().show_confirm_dialog("Apply Palette Confirmation", message)

        # Only accept the dialog if the user accepted the confirmation.
        if apply:
            QtWidgets.QDialog.accept(self)
            self.config.update(**self.updated)

    def iter_widgets(self):
        """
        Helper to iterate our palette selection widgets.
        """
        for palette_number in range(GAME_MAX_PALETTES):
            palette_id = palette_number_to_id(palette_number)

            # The attribute names of these combo boxes and buttons are explicitly defined in Qt Designer.
            # These attributes will in fact exist and we get at them this way to avoid writing a giant block of
            # code that would manually call out these widgets `GAME_MAX_PALETTES` times.
            palette_group = getattr(self.ui, PALETTE_GROUP_PREFIX.format(palette_id))
            select_combo = getattr(self.ui, SELECT_COMBOBOX_PREFIX.format(palette_id))

            yield palette_id, palette_group, select_combo

    def select_character(self):
        """
        A character was selected.
        We populate the palette selection widgets to reflect selections that were previously
        made and applied to the game for this character, as well as any saved palettes and current edits.
        """
        if not self.ui.palette_pages.isEnabled():
            self.ui.palette_pages.setEnabled(True)

        character = self.ui.character_select.currentData()
        has_sprites = bool(self.paths.get_sprite_cache(character))

        for palette_id, _, select_combo in self.iter_widgets():
            # TODO: we can probably improve "has edits" detection -> hashing?
            has_edits = bool(self.paths.get_edit_palette(character, palette_id))

            with block_signals(select_combo):
                select_combo.clear()
                # Allow the user to choose not to change this palette in game.
                select_combo.addItem(SLOT_NAME_NONE, PALETTE_NONE)

                # Only show the edit slot if sprites and palettes have been extracted
                # We have encounter a scenario where someone imports palettes without
                # editing or extracting any palettes on their own.
                if has_sprites and has_edits:
                    select_combo.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

                # Show any saved palettes that map to this palette ID.
                character_saves = self.paths.get_character_saves(character, palette_id)
                for save_name in character_saves:
                    select_combo.addItem(save_name, PALETTE_SAVE)

                select_name = self._get_palette_selected(character, palette_id)

                # If the config data is the initial value or "No Palette" value we pick the first item.
                # The first item in the selection combobox will always be the "No Palette" option.
                if select_name in (SLOT_NAME_INITIAL, SLOT_NAME_NONE):
                    select_combo.setCurrentIndex(0)
                    select_type = PALETTE_NONE
                    hpl_files = []

                # If the config data called out the edit slot we need to look for an associated edit slot..
                elif select_name in (SLOT_NAME_EDIT,):
                    index = select_combo.findData(PALETTE_EDIT)
                    select_combo.setCurrentIndex(normalize_index(index))
                    hpl_files = self.paths.get_edit_palette(character, palette_id)
                    select_type = PALETTE_EDIT

                # Otherwise we are working with a save name and need to ask the combo box what index is associated.
                else:
                    index = select_combo.findText(select_name)
                    select_combo.setCurrentIndex(normalize_index(index))
                    hpl_files = self.paths.get_saved_palette(character, palette_id, select_name)
                    select_type = PALETTE_SAVE

                # Update the selected state of this palette.
                self._mark_palette_selected(character, palette_id, select_name, select_type, hpl_files)

    def _update_sprite_preview(self, sprite_cache, hpl_files):
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
        return getattr(self.config, character + "_" + palette_id)

    def _mark_palette_selected(self, character, palette_id, select_name, select_type, hpl_files):
        """
        Update our selections that will be saved to disk in the apply config as well as
        the selections data we use to generate the data to apply to game files.
        Note that if the dialog is not accepted these datas are discarded.
        """
        self.updated[character + "_" + palette_id] = select_name

        if select_type == PALETTE_NONE:
            self.selected_palettes.pop((character, palette_id), None)

        else:
            self.selected_palettes[(character, palette_id)] = hpl_files

    def update_sprite_preview(self, palette_id, select_combo):
        """
        A character or palette selection was made and we need to update the UI.
        Note that if a palette selection of "No Palette" was made that we
        clear the graphics view and do not insert another image into it.
        """
        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

        select_type = select_combo.currentData()
        select_name = select_combo.currentText()

        character = self.ui.character_select.currentData()
        sprite_cache = self.paths.get_sprite_cache(character)

        # If there are no cached sprites we can't show a preview to the user.
        if not sprite_cache:
            character_name = self.ui.character_select.currentText()
            message = f"No Sprites for {character_name} have been extracted or edited!"
            self.parent().show_message_dialog("No Preview Available", message)
            return

        hpl_files = []

        if select_type == PALETTE_EDIT:
            hpl_files = self.paths.get_edit_palette(character, palette_id)

        if select_type == PALETTE_SAVE:
            hpl_files = self.paths.get_saved_palette(character, palette_id, select_name)

        self._mark_palette_selected(character, palette_id, select_name, select_type, hpl_files)

        # Only update the preview with a new image if we did not pick the "No Palette" slot.
        if select_type != PALETTE_NONE:
            self._update_sprite_preview(sprite_cache, hpl_files)

    def get_files_to_apply(self):
        """
        Helper method to create a dict of files to apply to the game that we can pass to ApplyThread.
        """
        files_to_apply = defaultdict(lambda: ([], []))

        # ApplyThread will attempt to insert game-version palettes to the PAC file it will
        # create based on the characters and palettes were (or were not) selected by the user.
        for (character, palette_id), hpl_files_list in self.selected_palettes.items():
            palettes, total_files_list = files_to_apply[character]
            total_files_list.extend(hpl_files_list)
            palettes.append(palette_id)

        return files_to_apply
