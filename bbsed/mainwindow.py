import io
import os
import re
import sys
import shutil
import subprocess

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libpac import enumerate_pac
from libhip import convert_from_hip
from libhpl import convert_to_hpl, replace_palette, get_palette_index

from .ui.mainwindow_ui import Ui_MainWindow

from .exceptions import AppError, AppException
from .settingsdialog import SettingsDialog
from .palettedialog import PaletteDialog
from .selectdialog import SelectDialog
from .zoomdialog import ZoomDialog
from .errordialog import ErrorDialog
from .config import Configuration
from .exporter import ExportThread
from .importer import ImportThread
from .extract import ExtractThread
from .apply import ApplyThread
from .pathing import Paths
from .char_info import *
from .util import *

BASE_WINDOW_TITLE = "BBCF Sprite Editor"
EDIT_MARKER_CHAR = "*"

HPL_IMPORT_REGEX = re.compile(r"([a-z]{2})(\d{2})_(\d{2})(" + PALETTE_EDIT_MARKER +
                              r"|(" + PALETTE_SAVE_MARKER + r"\w+))?" + PALETTE_EXT)
HPL_SAVE_REGEX = re.compile(PALETTE_SAVE_MARKER + r"(\w+)" + PALETTE_EXT)
HPL_EDIT_REGEX = re.compile(PALETTE_EDIT_MARKER + PALETTE_EXT)

NON_ALPHANUM_REGEX = re.compile(r"[^\w]")

HPL_MAX_PALETTES = GAME_MAX_PALETTES - 1
HPL_MAX_FILES_PER_PALETTE = 7


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

            settings[character][palette_id] = SLOT_NAME_NONE

    return settings


class ApplyConfig(Configuration):

    SETTINGS = generate_apply_settings()

    def __init__(self, paths):
        Configuration.__init__(self, paths.apply_config_file)


class AppConfig(Configuration):

    SETTINGS = {"bbsed": {"steam_install": ""}}

    def __init__(self, paths):
        Configuration.__init__(self, paths.app_config_file)
        # Set the config reference in the Paths object to this Configuration object.
        # We do this here to avoid a "chicken-and-egg" problem.
        paths.set_app_config(self)

    @property
    def steam_install(self):
        """
        Property to get the setting value from the config
        that will also make IDE introspection work correctly.
        """
        return getattr(self, "bbsed_steam_install")


# TODO: icons
# TODO: implement a help menu with About and Tutorial entries.
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(BASE_WINDOW_TITLE)

        self.paths = Paths()
        self.config = AppConfig(self.paths)
        self.apply_config = ApplyConfig(self.paths)
        self._check_steam_install()

        self.current_sprite = io.BytesIO()

        self.palette_dialog = PaletteDialog(self)
        self.palette_dialog.palette_data_changed.connect(self.update_palette)
        self.zoom_dialog = ZoomDialog(self)

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        # FIXME: there's something weird about drag select being off by one...
        self.ui.sprite_list.itemSelectionChanged.connect(self.select_sprite)
        self.ui.palette_select.currentIndexChanged[int].connect(self.select_palette)
        self.ui.slot_select.currentIndexChanged.connect(self.select_saved_palette)

        # Import and Export are always enabled as they are not dependent on palettes being loaded.
        # Delete and Discard are enabled/disabled separately from the remaining palette operations.
        self.ui.delete_palette.setEnabled(False)
        self.ui.discard_palette.setEnabled(False)
        self.set_palette_tools_enable(False)

        # We need to sort the character info before adding to the selection combo box.
        # This way the combo box index will match the defined character IDs in the char_info module.
        sorted_chars = list(CHARACTER_INFO.items())
        sorted_chars.sort(key=lambda item: item[0])

        for _, (character_name, character) in sorted_chars:
            self.ui.char_select.addItem(character_name, character)

        self.ui.char_select.setCurrentIndex(-1)
        self.ui.char_select.currentIndexChanged.connect(self.select_character)

        # Set out the sprite preview mouse events so we can update various app visuals.
        self.ui.sprite_preview.setMouseTracking(True)
        self.ui.sprite_preview.mouseDoubleClickEvent = self.set_palette_color
        self.ui.sprite_preview.mouseMoveEvent = self.move_zoom_cursor
        self.ui.sprite_preview.enterEvent = self.set_cross_cursor

        # File Menu
        self.ui.launch_bbcf.triggered.connect(self.launch_bbcf)
        self.ui.settings.triggered.connect(self.edit_settings)
        self.ui.exit.triggered.connect(self.exit_app)
        # View Menu
        self.ui.view_palette.triggered.connect(self.toggle_palette)
        self.ui.view_zoom.triggered.connect(self.toggle_zoom)
        # Game Files Toolbar and Menu
        self.ui.restore_all.triggered.connect(self.restore_all)
        self.ui.restore_character.triggered.connect(self.restore_character)
        self.ui.apply_palettes.triggered.connect(self.apply_palettes)
        # Edit Palette Toolbar and Menu
        self.ui.import_palettes.triggered.connect(self.import_palettes)
        self.ui.export_palettes.triggered.connect(self.export_palettes)
        self.ui.save_palette.triggered.connect(self.save_palette)
        self.ui.save_palette_as.triggered.connect(self.save_palette_as)
        self.ui.delete_palette.triggered.connect(self.delete_palette)
        # TODO: copy/paste here
        self.ui.discard_palette.triggered.connect(self.discard_palette)

    def set_palette_tools_enable(self, state):
        """
        Set the enable state of various palettes actions together.
        """
        self.ui.save_palette.setEnabled(state)
        self.ui.save_palette_as.setEnabled(state)
        self.ui.copy_palette.setEnabled(state)
        self.ui.paste_palette.setEnabled(state)

    def launch_bbcf(self, _):
        """
        Launch BBCF via Steam.
        """
        subprocess.call([self.paths.steam_exe, "-applaunch", BBCF_STEAM_APP_ID])

    def edit_settings(self, _):
        """
        Callback for the settings action. Display a dialog showing our app settings.
        """
        dialog = SettingsDialog(self.config, parent=self)
        dialog.exec_()

        # This will enable UI elements if we set a Steam install in the dialog.
        self._check_steam_install()

    def _check_steam_install(self):
        """
        Helper to check if we have a Steam install configured and should enable relevant UI elements.
        """
        if self.config.steam_install:
            self.ui.character_box.setEnabled(True)

    def exit_app(self, _):
        """
        Callback for the exit action. Close the window, which exits the app.
        """
        self.close()

    def closeEvent(self, evt):
        """
        Ensure we hide our dialogs when we close the main window or the app won't actually close.
        Unsure if calling the superclass closeEvent is required but we do so in case it is.
        """
        QtWidgets.QMainWindow.closeEvent(self, evt)
        self.palette_dialog.hide()
        self.zoom_dialog.hide()

    def _detect_nameless_hpl(self, hpl_file, save_name_map):
        """
        Look for HPL files we are attempting to import that do not have a bbsed save marker.
        If we find such a file we ask the user for a name to associate to the imported files on
        a character/palette ID basis.
        We return the key which is used to get a palette named associated to a given HPL file.
        """
        # We might get a full path or basename file name as input.
        hpl_file = os.path.basename(hpl_file)

        character = hpl_file[:CHAR_ABBR_LEN]
        palette_num = hpl_file[CHAR_ABBR_LEN:CHAR_ABBR_LEN+PALETTE_ID_LEN]
        palette_id = palette_number_to_id(palette_num)
        palette_name_key = (character, palette_id)

        is_nameless = PALETTE_EDIT_MARKER not in hpl_file and PALETTE_SAVE_MARKER not in hpl_file
        is_edit = PALETTE_EDIT_MARKER in hpl_file
        is_save = PALETTE_SAVE_MARKER in hpl_file

        # We have found an unnamed palette. Choose a name for it!
        if is_nameless and palette_name_key not in save_name_map:
            palette_name, accepted = self._choose_palette_name(character, palette_id, *save_name_map.values())

            if not accepted:
                message = "Did not specify import save name! Aborting import!"
                raise AppError("Palette Name Required", message)

            save_name_map[palette_name_key] = palette_name

        # If the user previously chosen a name that applies to this file we should use it.
        elif is_nameless and palette_name_key in save_name_map:
            palette_name = save_name_map[palette_name_key]

        elif is_save:
            # If we have a save marker then we can use that to get the palette name.
            save_match = HPL_SAVE_REGEX.search(hpl_file)
            palette_name = save_match.group(1)

        elif is_edit:
            palette_name = EDIT_INTERNAL_NAME

        else:
            # We should never get here, but it makes IDEs and PyLint not complain
            # about `palette_name` potentially not being defined.
            raise AppError("Import Error Condition", f"Bad file name {hpl_file}!")

        return character, palette_id, palette_name

    @staticmethod
    def _validate_hpl_file(hpl_file):
        """
        Helper method to ensure the given HPL palette file is valid to the best of our ability.
        """
        # Assert that the import HPL file has the correct extension.
        if not hpl_file.endswith(PALETTE_EXT):
            message = "Imported HPL palettes must have extension '.hpl'!"
            raise AppError("Invalid HPL Palette File!", message)

        # Assert that imported HPL files must have file names that match the names we would see in
        # game data so we know which cache directory to import the files to.
        format_match = HPL_IMPORT_REGEX.search(hpl_file)
        if format_match is None:
            message = "Imported HPL palettes must have name format matching game data!\n\nExample:\n\nam00_00.hpl"
            raise AppError("Invalid HPL Palette File!", message)

        # Assert that the file name starts with a valid character abbreviation.
        # If it does not we cannot know where to put the data in the cache or where to apply the file
        # to the actual game data.
        abbreviation = format_match.group(1)
        if abbreviation not in VALID_CHARACTERS:
            message = f"HPL file name {hpl_file} does not begin with a known character abbreviation!"
            raise AppError("Invalid HPL Palette File!", message)

        # Assert that the palette index is valid.
        palette_index = int(format_match.group(2))
        if palette_index < 0 or palette_index > HPL_MAX_PALETTES:
            message = f"HPL palette index must 00 to {HPL_MAX_PALETTES}!"
            raise AppError("Invalid HPL Palette File!", message)

        # Assert that the palette file number is valid.
        file_number = int(format_match.group(3))
        if file_number < 0 or file_number > HPL_MAX_FILES_PER_PALETTE:
            message = f"HPL file number must be 00 to {HPL_MAX_FILES_PER_PALETTE:02}!"
            raise AppError("Invalid HPL Palette File!", message)

    def _scan_single_hpls(self, hpl_file_list, save_name_map):
        """
        Look for nameless HPL files in the HPL file selection list.
        We also perform basic validation on the files to ensure there are no formatting issues.

        We assume that we can't pick individual HPL files with the same name because
        files cannot exist on disk with the same name and we don't allow for picking from
        mulitple directories at the same time.

        NTFS is not a case sensitive file system (which frankly is quite stupid), but our
        validation regex is case sensitive so we eliminate the possibility of duplicate
        individual HPL files during import.
        """
        hpl_to_import = defaultdict(list)

        for hpl_full_path in hpl_file_list:
            hpl_file = os.path.basename(hpl_full_path)
            self._validate_hpl_file(hpl_file)

            key = self._detect_nameless_hpl(hpl_full_path, save_name_map)
            hpl_to_import[key].append(hpl_full_path)

        return hpl_to_import

    def _scan_pac(self, pac_full_path, hpl_file_list, save_name_map):
        """
        Enumerate the given PAC file and look for embedded nameless HPL files.
        We perform basic validation on the HPL file names and look for HPL file names that
        collide with any individually selected HPL files to avoid import issues.
        """
        individual_hpl_files = [os.path.basename(hpl_full_path) for hpl_full_path in hpl_file_list]

        hpl_to_import = defaultdict(list)
        enumerated_hpl_files = set()

        try:
            file_list = enumerate_pac(pac_full_path)

        except Exception:
            message = f"Failed to get files list from {pac_full_path}! Aborting import!"
            raise AppException("Error Enumerating PAC File", message)

        for hpl_file, _, __, __ in file_list:
            self._validate_hpl_file(hpl_file)

            if hpl_file in individual_hpl_files:
                message = f"HPL file name ({hpl_file}) in {pac_full_path} matches manual HPL file selection!"
                raise AppError("PAC Palette HPL File Collision!", message)

            if hpl_file in enumerated_hpl_files:
                message = f"Duplicate HPL file name ({hpl_file}) found in {pac_full_path}!"
                raise AppError("Invalid PAC Palette File!", message)

            key = self._detect_nameless_hpl(hpl_file, save_name_map)
            hpl_to_import[key].append(hpl_file)

            enumerated_hpl_files.add(hpl_file)

        return hpl_to_import

    def _scan_imports(self, hpl_file_list, pac_file_list):
        """
        Determine if we need to get user input for some of our files selected for import
        and/or if some of those files are not valid for import.
        """
        save_name_map = {}

        hpl_to_import = self._scan_single_hpls(hpl_file_list, save_name_map)

        pac_to_import = {}
        for pac_full_path in pac_file_list:
            pac_to_import[pac_full_path] = self._scan_pac(pac_full_path, hpl_file_list, save_name_map)

        return hpl_to_import, pac_to_import

    @staticmethod
    def _parse_palette_list(palette_file_list):
        """
        Split up our files by type so we can perform different operations on them.
        """
        hpl_file_list = []
        pac_file_list = []

        for palette_full_path in palette_file_list:
            if palette_full_path.endswith(PALETTE_EXT):
                hpl_file_list.append(palette_full_path)

            elif palette_full_path.endswith(GAME_PALETTE_EXT):
                pac_file_list.append(palette_full_path)

            else:
                _, ext = os.path.splitext(palette_full_path)
                message = f"Unknown palette file type {ext}!"
                raise AppError("Unknown Palette File Type", message)

        return hpl_file_list, pac_file_list

    def import_palettes(self, _):
        """
        Callback for the palette import action. Allow the user to import palettes they may have
        created prior to using this tool or palettes they received from friends :D
        """
        palette_file_list, _ = QtWidgets.QFileDialog.getOpenFileNames(

            parent=self,
            caption="Select Palette Files",
            filter="BBCF palettes (*.hpl; *.pac);;HPL files (*.hpl);;PAC files (*.pac)"
        )

        # NOTE: if we cancel the dialog then `palette_file_list` will be empty.

        try:
            hpl_file_list, pac_file_list = self._parse_palette_list(palette_file_list)
            hpl_to_import, pac_to_import = self._scan_imports(hpl_file_list, pac_file_list)

        # If we encountered a problem during import we should not continue.
        except AppError as error:
            self.show_message_dialog(*error.get_details())
            return

        # Don't run any thread's if we do not need to.
        if hpl_to_import or pac_to_import:
            thread = ImportThread(hpl_to_import, pac_to_import, self.paths)
            success = self.run_work_thread(thread, "Palette Importer", "Validating palette files...")

            # If the import succeeded we should check if we need to update the UI:
            if success:
                character = self.ui.char_select.currentData()
                palette_id = self.ui.palette_select.currentText()

                # Update the save slots to include the newly imported files, but only if we have imported
                # palettes for the current selected character and palette ID.
                with block_signals(self.ui.slot_select):
                    for save_char, save_pal_id, save_name in hpl_to_import.keys():
                        if save_char == character and save_pal_id == palette_id:
                            self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

                    for file_info in pac_to_import.values():
                        for save_char, save_pal_id, save_name in file_info.keys():
                            if save_char == character and save_pal_id == palette_id:
                                self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

                # We can discard changes without actually having picked a sprite.
                selected_sprite = self.ui.sprite_list.currentItem()
                if selected_sprite is not None:
                    self._update_sprite_preview()

    def _choose_export_pac(self):
        """
        Helper to get the export PAC file path which will be our export destination.
        """
        pac_path, _ = QtWidgets.QFileDialog.getSaveFileName(

            parent=self,
            caption="Select Palette Export directory",
            filter="PAC files (*.pac)"
        )

        return pac_path

    def export_palettes(self):
        """
        Callback for the Export All action. Share all your palettes with friends :D
        """
        pac_path = self._choose_export_pac()

        if pac_path:
            dialog = SelectDialog(self.paths, allow_multi_select=True, parent=self)
            export = dialog.exec_()

            # If we accepted the dialog then we should actually create the export.
            if export:
                thread = ExportThread(pac_path, dialog.get_selected_palettes(), self.paths)
                self.run_work_thread(thread, "Palette Exporter", "Exporting Palette Data...")

    def toggle_palette(self, check_state):
        """
        Callback for our palette toggle action. Set the visibility state of the palette dialog.
        Mostly useful for recovering the dialog if it was closed, but maybe some folks wanna hide it anyway.
        """
        self.palette_dialog.setVisible(check_state)

    def set_palette_visibility(self, is_visible):
        """
        Show or hide the palette dialog and update the view palette action check state to match.
        """
        self.palette_dialog.setVisible(is_visible)
        self.ui.view_palette.setChecked(is_visible)

    def toggle_zoom(self, check_state):
        """
        Callback for our zoom toggle action. Set the visibility state of the zoom dialog.
        Mostly useful for recovering the dialog if it was closed, but maybe some folks wanna hide it anyway.
        """
        self.zoom_dialog.setVisible(check_state)

    def set_zoom_visibility(self, is_visible):
        """
        Show or hide the zoom dialog and update the view zoom action check state to match.
        """
        self.zoom_dialog.setVisible(is_visible)
        self.ui.view_zoom.setChecked(is_visible)

    def apply_palettes(self, _):
        """
        Callback for the Apply All action. Apply all palettes to the BBCF game data.
        """
        dialog = SelectDialog(self.paths, config=self.apply_config, parent=self)
        selection_made = dialog.exec_()

        if selection_made:
            message = "Do you wish to apply the selected palettes to the BBCF game files?"
            confirmed = self.show_confirm_dialog("Apply Palette Confirmation", message)

            if confirmed:
                thread = ApplyThread(dialog.get_selected_palettes(), self.paths)
                self.run_work_thread(thread, "Sprite Updater", "Applying Sprite Data...")

    def discard_palette(self, _):
        """
        Discard the any edited palette files.
        """
        character = self.ui.char_select.currentData()
        character_name = self.ui.char_select.currentText()
        palette_id = self.ui.palette_select.currentText()

        message = f"Do you wish to discard edits for {character_name} palette {palette_id}?"
        discard = self.show_confirm_dialog("Discard Edited Palette", message)

        if discard:
            hpl_hash_list = self.paths.get_edit_palette_hashes(character, palette_id)

            for hpl_full_path, edit_hash, orig_hash in hpl_hash_list:
                is_dirty = (edit_hash != orig_hash)

                # If the hashes don't match then the file was edited.
                # In this case where we are discarding changes we then remove
                # the palette file and copy the backup in place of it.
                if is_dirty:
                    os.remove(hpl_full_path)
                    backup_full_path = hpl_full_path.replace(PALETTE_EXT, BACKUP_PALETTE_EXT)
                    shutil.copyfile(backup_full_path, hpl_full_path)

            # Remove the edit marker from the window title.
            self.setWindowTitle(BASE_WINDOW_TITLE + f" - {character_name} - {palette_id}")
            self.ui.discard_palette.setEnabled(False)

            # We can discard changes without actually having picked a sprite.
            selected_sprite = self.ui.sprite_list.currentItem()
            if selected_sprite is not None:
                self._update_sprite_preview()

    def _restore_character_palettes(self, character):
        """
        Helper to delete the existing PAC palette file and replace it with the backed version from the game data.
        """
        backup_palette_name = BACKUP_PALETTE_FILE_FMT.format(character)
        backup_palette_path = os.path.join(self.paths.bbcf_data_dir, backup_palette_name)

        # If a backup does not exist then we should not attempt restore as legitimately can't do it.
        if not os.path.exists(backup_palette_path):
            return

        pac_palette_name = PALETTE_FILE_FMT.format(character)
        pac_palette_path = os.path.join(self.paths.bbcf_data_dir, pac_palette_name)

        os.remove(pac_palette_path)
        shutil.copyfile(backup_palette_path, pac_palette_path)

    def restore_all(self, _):
        """
        Restore all character palettes from the backed up game data in the BBCF install directory.
        """
        message = "Do you wish to restore all game files to the original versions?"
        restore = self.show_confirm_dialog("Restore Game Files", message)

        if restore:
            for character in VALID_CHARACTERS:
                self._restore_character_palettes(character)

    def restore_character(self, _):
        """
        Restore the selected character palettes from the backed up game data in the BBCF install directory.
        """
        character_name = self.ui.char_select.currentText()

        message = f"Do you wish to restore game files for {character_name} to the original versions?"
        restore = self.show_confirm_dialog("Restore Game Files", message)

        if restore:
            character = self.ui.char_select.currentData()
            self._restore_character_palettes(character)

    def _save_palette(self, palette_name):
        """
        Save the current palette with the given name.
        We will be able to recall and export this palette after it is saved.
        """
        character = self.ui.char_select.currentData()
        palette_id = self.ui.palette_select.currentText()

        save_dst_path = self.paths.get_character_save_path(character, palette_id, palette_name)
        if not os.path.exists(save_dst_path):
            os.makedirs(save_dst_path)

        slot_type = self.ui.slot_select.currentData()

        if slot_type == PALETTE_EDIT:
            files_to_save = self.paths.get_edit_palette(character, palette_id)

        else:
            save_name = self.ui.slot_select.currentText()
            files_to_save = self.paths.get_saved_palette(character, palette_id, save_name)

        for hpl_src_path in files_to_save:
            hpl_file = os.path.basename(hpl_src_path)

            hpl_dst_path = os.path.join(save_dst_path, hpl_file)
            shutil.copyfile(hpl_src_path, hpl_dst_path)

            # If we are saving an already saved palette under a new name we should not delete the source files.
            if slot_type == PALETTE_EDIT:
                os.remove(hpl_src_path)
                backup_full_path = hpl_src_path.replace(PALETTE_EXT, BACKUP_PALETTE_EXT)
                shutil.copyfile(backup_full_path, hpl_src_path)

        # Add this palette to the selectable saved palettes and select it.
        with block_signals(self.ui.slot_select):
            self.ui.slot_select.addItem(palette_name, PALETTE_SAVE)
            new_index = self.ui.slot_select.findText(palette_name)
            self.ui.slot_select.setCurrentIndex(new_index)

        # If this is the first palette saved for this character and palette ID then we will need to enable
        # the save select combobox.
        if not self.ui.slot_select.isEnabled():
            self.ui.slot_select.setEnabled(True)

    def _choose_palette_name(self, character, palette_id, *previous_choices):
        """
        Helper method to show an input dialog to select the name for a palette
        that we either created ourselves or are importing from something else.

        The caller can optionally provide an HPL file name to display in the dialog
        so the user has an idea of what palette they are naming. This is mostly useful
        for importing PAC or HPL files that do not come from a bbsed export.

        We provide *args for previous palette name choices as in certain scenarios we
        may need to choose a name multiple time during a single operation (like import).
        """
        existing_saves = self.paths.get_character_saves(character, palette_id)

        index = self.ui.char_select.findData(character)
        character_name = self.ui.char_select.itemText(index)

        while True:
            flags = QtCore.Qt.WindowType.WindowTitleHint
            message = f"Choose a name for your palette ({character_name} - {palette_id}):"
            palette_name, accepted = QtWidgets.QInputDialog.getText(self, "Name Your Palette", message, flags=flags)

            # Restrict palette names to alphanumeric characters and underscore.
            # However if the dialog is not accepted we ignore this restriction as we will be discarding this data.
            if NON_ALPHANUM_REGEX.search(palette_name) is not None and accepted:
                message = "Palette names may only contain alpha-numeric characters and underscores!"
                self.show_message_dialog("Invalid Palette Name", message, QtWidgets.QMessageBox.Icon.Critical)

            # If the palette name already exists and the dialog was accepted we should
            # show a message and not overwrite any data that exists under this name.
            # If the dialog was not accepted we ignore this restriction as we will be discarding this data.
            elif palette_name in existing_saves and accepted:
                message = f"Palette name {palette_name} already exists!"
                self.show_message_dialog("Invalid Palette Name", message, QtWidgets.QMessageBox.Icon.Critical)

            # If the palette name was recently chosen as an import name then
            # show a message and not overwrite any data that exists under this name.
            # If the dialog was not accepted we ignore this restriction as we will be discarding this data.
            elif palette_name in previous_choices and accepted:
                message = f"Palette name {palette_name} was previously chosen for other palettes!"
                self.show_message_dialog("Invalid Palette Name", message, QtWidgets.QMessageBox.Icon.Critical)

            # We picked a good name or the dialog was not accepted.
            else:
                return palette_name, accepted

    def save_palette(self, _):
        """
        Save the current palette to disk.
        """
        character = self.ui.char_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        slot_type = self.ui.slot_select.currentData()

        # If we have a saved palette selected we keep the name previously chosen.
        if slot_type == PALETTE_SAVE:
            palette_name = self.ui.slot_select.currentText()

        # If we have the edit slot selected then we prompt the user to choose a name.
        else:
            palette_name, accepted = self._choose_palette_name(character, palette_id)

            # If we did not accept the dialog then we do not want to save the palette.
            if not accepted:
                return

        self._save_palette(palette_name)

    def save_palette_as(self, _):
        """
        Save the current palette to disk. We will always prompt the user for a name.
        """
        character = self.ui.char_select.currentData()
        palette_id = self.ui.palette_select.currentText()

        palette_name, accepted = self._choose_palette_name(character, palette_id)

        # If we did not accept the dialog then we do not want to save the palette.
        if not accepted:
            return

        self._save_palette(palette_name)

    def delete_palette(self, _):
        """
        Delete the current selected saved palette.
        """
        palette_id = self.ui.palette_select.currentText()

        save_index = self.ui.slot_select.currentIndex()
        save_name = self.ui.slot_select.currentText()

        message = f"Do you want to delete saved palette {save_name}?"
        delete = self.show_confirm_dialog("Delete Palette", message)

        if delete:
            with block_signals(self.ui.slot_select):
                self.ui.slot_select.removeItem(save_index)

            character = self.ui.char_select.currentData()
            save_dst_path = self.paths.get_character_save_path(character, palette_id, save_name)
            shutil.rmtree(save_dst_path)

            # Re-select the edit slot after we delete a palette.
            self.ui.slot_select.setCurrentIndex(0)

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

    def _update_sprite_preview(self, palette_index=None):
        """
        Update the sprite preview with the given palette index.
        If no index is provided we assume that the current index is to be used.
        This method is only invoked when we pick a new sprite or select a new palette.
        Our cached sprite uses a palette from the sprite data definition, NOT from the
        in-game palette data. This means that we should always be re-writing the palette.
        """
        if palette_index is None:
            palette_index = self.ui.palette_select.currentIndex()

        palette_id = self.ui.palette_select.itemText(palette_index)
        slot_type = self.ui.slot_select.currentData()
        character = self.ui.char_select.currentData()

        # If we have a saved palette selected we should display that palette.
        if slot_type == PALETTE_SAVE:
            save_name = self.ui.slot_select.currentText()
            hpl_files = self.paths.get_saved_palette(character, palette_id, save_name)

        # Otherwise display the edit slot data.
        else:
            hpl_files = self.paths.get_edit_palette(character, palette_id)

        # FIXME: how do we determine which file is for what? e.g. izayoi phorizor?
        #        for now just assume that the first palette is the one that matters, as that is true frequently.
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

        # Update the dialog palette data since we have switched palettes.
        # NOTE: When the dialog emits palette_data_changed... we end up here... we should change that eventually.
        self.palette_dialog.set_palette(palette_full_path)
        # Update the zoom dialog to the current sprite.
        self.zoom_dialog.set_sprite(self.current_sprite)
        # Do not show the palette or zoom dialogs until after we have set the palette/sprite information on them.
        # If we show them prior to this then the dialog graphics view does not correctly update
        # until we change the current palette.

        # Show our palette dialog if we need to.
        if self.palette_dialog.isHidden():
            self.set_palette_visibility(True)

        # Show our zoom dialog if we need to.
        if self.zoom_dialog.isHidden():
            self.set_zoom_visibility(True)

    def move_zoom_cursor(self, evt):
        x = evt.x()
        y = evt.y()

        mapped_point = self.ui.sprite_preview.mapToScene(Qt.QPoint(x, y))
        self.zoom_dialog.move_cursor(mapped_point)

    def set_palette_color(self, evt):
        x = evt.x()
        y = evt.y()

        mapped_point = self.ui.sprite_preview.mapToScene(Qt.QPoint(x, y))

        try:
            palette_index = get_palette_index(self.current_sprite, (mapped_point.x(), mapped_point.y()))

        except Exception:
            self.show_error_dialog("Error Getting Palette Index", f"Failed to get palette index of selected color!")
            return

        self.palette_dialog.set_palette_index(palette_index)

    def set_cross_cursor(self, _):
        self.ui.sprite_preview.viewport().setCursor(QtCore.Qt.CursorShape.CrossCursor)

    def update_palette(self):
        """
        The color in a palette has been changed by the user. Save the changes to disk.
        """
        palette_id = self.ui.palette_select.currentText()
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()
        hpl_files = self.paths.get_edit_palette(character, palette_id)

        # FIXME: see other FIXME about HPL files
        palette_full_path = hpl_files[0]

        try:
            convert_to_hpl(self.palette_dialog.get_palette_img(), palette_full_path)

        except Exception:
            message = f"Failed to update palette {palette_id} for {character_name}!"
            self.show_error_dialog("Error Updating Palette", message)
            return

        # Add a marker to the window that indicates the user has active changes.
        self.setWindowTitle(BASE_WINDOW_TITLE + f" - {character_name} - {palette_id}{EDIT_MARKER_CHAR}")
        self.ui.discard_palette.setEnabled(True)

        # Get the type of slot upon which we just made changes.
        slot_type = self.ui.slot_select.currentData()

        # FIXME: right meow this information will not be persistent if we switch character or palette, or close
        #        the app. We will be able to determine the edit slot was changed but that is it. we need to store
        #        meta data about the slot type/save name with this change.
        # If we are working on a save slot then we need to switch to the edit slot to see our active changes.
        # Setting the slot select index will trigger a preview update.
        if slot_type == PALETTE_SAVE:
            self.ui.slot_select.setCurrentIndex(0)

        # Otherwise we have to trigger the preview update manually.
        else:
            self._update_sprite_preview()

    def select_sprite(self):
        """
        A new sprite has been selected.
        Update our image preview with the new sprite.
        """
        selected_sprite = self.ui.sprite_list.currentIndex()
        character = self.ui.char_select.currentData()

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

        try:
            self._update_sprite_preview()

        except Exception:
            self.show_error_dialog("", "")
            return

    def _update_title_for_palette(self, character, palette_id, character_name):
        """
        Helper to update the window title based on presence of active changes from the user.
        """
        window_title = BASE_WINDOW_TITLE + f" - {character_name} - {palette_id}"
        self.ui.discard_palette.setEnabled(False)

        # Look for any palette files with active changes.
        for _, edit_hash, orig_hash in self.paths.get_edit_palette_hashes(character, palette_id):
            is_dirty = (edit_hash != orig_hash)

            # If the loaded character/palette has active changes our new window title should include the edit marker.
            if is_dirty:
                window_title += EDIT_MARKER_CHAR
                self.ui.discard_palette.setEnabled(True)
                break

        self.setWindowTitle(window_title)

    def select_palette(self, index):
        """
        A new palette has been selected.
        Replace the palette of the currently selected sprite and update the image preview.
        """
        selected_sprite = self.ui.sprite_list.currentItem()
        character = self.ui.char_select.currentData()
        character_name = self.ui.char_select.currentText()
        palette_id = self.ui.palette_select.currentText()

        self._update_title_for_palette(character, palette_id, character_name)

        # When we select a palette ID we need to look for existing saved palettes associated to it.
        # Based on the presence of these files we also need to update the state of the UI.
        character_saves = self.paths.get_character_saves(character, palette_id)

        with block_signals(self.ui.slot_select):
            # Disable delete while we do not have a selected saved palette.
            self.ui.delete_palette.setEnabled(False)
            # Clearing the save select and re-adding items will auto-select the first item
            # which will always be a non-saved palette.
            self.ui.slot_select.clear()
            self.ui.slot_select.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

            # Set the save select enable state based on the presence of files on disk.
            self.ui.slot_select.setEnabled(bool(character_saves))
            for save_name in character_saves:
                self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

        # Only update the preview if we have a selected sprite and we have also have a selected palette.
        if selected_sprite is not None and index >= 0:
            self._update_sprite_preview(index)

    def select_saved_palette(self):
        """
        We have selected a palette which has been saved by the user.
        """
        # Disable the delete button when we have the Edit slot selected.
        can_delete = self.ui.slot_select.currentData() == PALETTE_SAVE
        self.ui.delete_palette.setEnabled(can_delete)

        # Only update the preview if we have a selected sprite.
        # We cannot get here without first selecting a palette.
        selected_sprite = self.ui.sprite_list.currentItem()
        if selected_sprite is not None:
            self._update_sprite_preview()

    def _reset_ui(self):
        """
        Reset the state of the UI. This includes clearing all graphics views, emptying the selectable
        sprite file list, and resetting combo box selections. We also clear meta data associated to these things.
        """
        with block_signals(self.ui.palette_select):
            self.ui.palette_select.setCurrentIndex(-1)

        with block_signals(self.ui.sprite_list):
            self.ui.sprite_list.clear()

        with block_signals(self.ui.slot_select):
            self.ui.delete_palette.setEnabled(False)
            self.ui.slot_select.setEnabled(False)
            self.ui.slot_select.clear()
            self.ui.slot_select.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

        self.setWindowTitle(BASE_WINDOW_TITLE)
        self.ui.discard_palette.setEnabled(False)

        self._clear_sprite_data()

    def select_character(self):
        """
        A new character was picked from the character combobox.
        """
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()

        # Don't allow the user to interact with these parts of the UI while we are updating them.
        self.ui.sprite_group.setEnabled(False)

        # Reset all the things. This method actually has the deselect_character argument specifically
        # so we can use it here without immediately deselecting the character we just picked.
        self._reset_ui()

        # Extract the character data.
        thread = ExtractThread(character, self.paths)
        if not self.run_work_thread(thread, "Sprite Extractor", "Extracting Sprite Data..."):
            # If our extract did not succeed we de-select the character and do not load any further data.
            with block_signals(self.ui.char_select):
                self.ui.char_select.setCurrentIndex(-1)
                return

        # Reset our HIP file list and add the new HIP files so we only have the currently selected character files.
        with block_signals(self.ui.sprite_list):
            sprite_cache = self.paths.get_sprite_cache(character)
            ui_sprite_cache = [os.path.basename(sprite_full_path) for sprite_full_path in sprite_cache]
            self.ui.sprite_list.addItems(ui_sprite_cache)

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
        with block_signals(self.ui.slot_select):
            character_saves = self.paths.get_character_saves(character, palette_id)
            # Set the save select enable state based on the presence of files on disk.
            self.ui.slot_select.setEnabled(bool(character_saves))
            for save_name in character_saves:
                self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

        # Re-enable user interaction for everything else.
        self.ui.sprite_group.setEnabled(True)
        # If our menus and toolbars are disabled (like it is at app launch) we should now enable it.
        # At launch it is disabled due to the fact that we will not have a selected character or palette.
        # If the user clicks any of the buttons with no character or palette selected then bad things happen.
        # Note that we set the state of the menus and toolbars together so we can just check the toolbar state
        # here to probe the enable state of both UI elements.
        if not self.ui.save_palette_as.isEnabled():
            self.set_palette_tools_enable(True)

        self._update_title_for_palette(character, palette_id, character_name)

    def show_confirm_dialog(self, title, message):
        """
        Ask the user to confirm an operation.
        We set the default button to No so it is more difficult to accidentally accept the dialog.
        Return a bool indicating if the dialog was accepted or rejected.
        """
        icon = QtWidgets.QMessageBox.Icon.Question

        message_box = QtWidgets.QMessageBox(icon, title, message, parent=self)
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)

        # The return value for the `exec_()` method on a QMessageBox is the button type enum of the clicked button.
        # Note that if the user exits the dialog with the escape key that we will still return `False`.
        return message_box.exec_() == QtWidgets.QMessageBox.Yes

    def show_message_dialog(self, title, message, icon=QtWidgets.QMessageBox.Icon.NoIcon):
        """
        Show a message to the user.
        """
        message_box = QtWidgets.QMessageBox(icon, title, message, parent=self)
        message_box.exec_()

    def show_error_dialog(self, title, message, exc_info=None):
        """
        Show a dialog for an error that just occurred.
        We should not fail any operations silently.
        Note that this method must be called within an `except:` block if `exc_info` is None.
        """
        if exc_info is None:
            exc_info = sys.exc_info()

        dialog = ErrorDialog(title, message, exc_info, parent=self)
        dialog.exec_()

    def run_work_thread(self, thread, title, initial_message):
        """
        Helper to run a thread and do some work (that will likely take a long time) so it does not block the UI.
        """
        # Create a busy-progress-bar dialog box so the user knows the app is doing something.
        # We set the window flags to remove buttons and the like so the user cannot close it.
        # Maybe this is a bad idea in the case of error conditions but we should not get stuck
        # due to how we set up our signals in a bit.
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        # Set the label, min and max progress value (max of 0 is how we get a busy-bar), dialog parent, and flags.
        dialog = QtWidgets.QProgressDialog(initial_message, "", 0, 0, parent=self, flags=flags)
        dialog.setWindowTitle(title)
        # Remove the cancel button. This dialog cancels itself (sortof).
        dialog.setCancelButton(None)

        def _set_message(_message):
            dialog.setLabelText(_message)

        # Connecting signals with a BlockingQueuedConnection is a requirement for thread safety.
        # We connect a custom signal to set the message of the dialog so the worker thread can update the
        # status of the operation for the user.
        thread.message.connect(_set_message, QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        # We connect the thread finished signal so we can have the dialog automatically close when the thread
        # terminates and thus not worry about closing the dialog ourselves.
        thread.finished.connect(dialog.cancel, QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        thread.start()

        # Show our dialog and once it closes we ensure our thread is joined.
        dialog.exec_()
        thread.wait()

        # If we have a standard error display it to the user with a normal message dialog.
        if thread.error is not None:
            self.show_message_dialog(*thread.error.get_details())

        # If we have an exceptional error display it to the user with an error dialog (i.e. show a traceback).
        if thread.exc is not None:
            self.show_error_dialog(*thread.exc.get_details())

        # Return the success status of the thread. A thread is considered successful if no errors, exceptional
        # or otherwise, were encountered while performing the work procedure.
        return thread.error is None and thread.exc is None
