import os
import re
import sys
import shutil
import subprocess

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libpac import enumerate_pac

from .ui.main_window_ui import Ui_MainWindow

from .exceptions import AppError, AppException
from .settings_dialog import SettingsDialog
from .tutorial_dialog import TutorialDialog
from .select_dialog import SelectDialog
from .sprite_editor import SpriteEditor
from .about_dialog import AboutDialog
from .error_dialog import ErrorDialog
from .config import Configuration
from .exporter import ExportThread
from .importer import ImportThread
from .extract import ExtractThread
from .apply import ApplyThread
from .pathing import Paths
from .char_info import *
from .util import *

WINDOW_TITLE_BASE = "BBCF Sprite Editor"
WINDOW_TITLE_EXTRA = " - {} - {}"
WINDOW_TITLE_SLOT = " - {}"
WINDOW_TITLE_EDIT_MARK = "*"

HPL_IMPORT_REGEX = re.compile(r"([a-z]{2})(\d{2})_(\d{2})(" + PALETTE_SAVE_MARKER + r"\w+)?" + PALETTE_EXT)
HPL_SAVE_REGEX = re.compile(PALETTE_SAVE_MARKER + r"(\w+)" + PALETTE_EXT)

PALETTE_NUM_REGEX = re.compile(r"(\w{2})(\d{2})_(\d{2})")
SLOT_NAME_REGEX = re.compile(r".\w+.hpl")

NON_ALPHANUM_REGEX = re.compile(r"[^\w]")

PALETTE_NUM_REPL = r"\g<1>{}_\g<3>"

HPL_MAX_PALETTES = GAME_MAX_PALETTES - 1
HPL_MAX_FILES_PER_PALETTE = 7

MAX_UNHANDLED_DIALOGS = 1


def generate_palette_settings():
    """
    Generate the settings definition of ApplyConfig
    programmatically to save codespace.
    """
    settings = {}

    for character in VALID_CHARACTERS:
        settings[character] = {}

        for palette_id, palette_num in iter_palettes():
            settings[character][palette_id] = SLOT_NAME_BBCF

    return settings


class SelectConfig(Configuration):

    SETTINGS = generate_palette_settings()

    def __init__(self, paths):
        Configuration.__init__(self, paths.select_config_file)


class AppliedConfig(Configuration):

    SETTINGS = generate_palette_settings()

    def __init__(self, paths):
        Configuration.__init__(self, paths.applied_config_file)


class AppConfig(Configuration):

    SETTINGS = {"bbsed": {"steam_install": ""}}

    def __init__(self, paths):
        Configuration.__init__(self, paths.app_config_file)
        # Set the config reference in the Paths object to this Configuration object.
        # We do this here to avoid a "chicken-and-egg" problem.
        paths.set_app_config(self)


class MainWindow(QtWidgets.QMainWindow):

    unhandled_exc = QtCore.pyqtSignal(tuple)

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(Qt.QIcon(":/images/images/app.png"))
        self._set_window_title()

        self.paths = Paths()
        self.app_config = AppConfig(self.paths)
        self.select_config = SelectConfig(self.paths)
        self.applied_config = AppliedConfig(self.paths)

        self.clipboard = None

        # Only allow one unhandled error dialog at a time.
        self.unhandled_sem = QtCore.QSemaphore(n=MAX_UNHANDLED_DIALOGS)

        self.sprite_editor = SpriteEditor(self, self.paths, self.ui.central_widget)
        self.sprite_editor.image_data_changed.connect(self.update_ui_for_palette)
        self.sprite_editor.character_changed.connect(self.character_changed)
        self.sprite_editor.palette_changed.connect(self.palette_changed)
        self.sprite_editor.palette_slot_changed.connect(self.palette_slot_changed)

        sprite_layout = self.ui.central_widget.layout()
        sprite_layout.addWidget(self.sprite_editor)

        # Import and Export are always enabled as they are not dependent on palettes being loaded.
        # Delete, Discard, and Paste are enabled/disabled separately from the remaining palette operations.
        self.ui.delete_palette.setEnabled(False)
        self.ui.discard_palette.setEnabled(False)
        self.ui.paste_palette.setEnabled(False)
        self.set_palette_tools_enable(False)

        # File Menu
        self.ui.launch_bbcf.triggered.connect(self.launch_bbcf)
        self.ui.settings.triggered.connect(self.edit_settings)
        self.ui.exit.triggered.connect(self.exit_app)
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
        self.ui.copy_palette.triggered.connect(self.copy_palette)
        self.ui.paste_palette.triggered.connect(self.paste_palette)
        self.ui.discard_palette.triggered.connect(self.discard_palette)
        # Help Menu
        self.ui.tutorial.triggered.connect(self.show_tutorial)
        self.ui.about.triggered.connect(self.show_about_dialog)

        # Check if we should enable some editor UI elements at startup.
        self._check_steam_install()

    def _unhandled_exc(self, exc_info):
        """
        Display an unhandled error.
        Note that we use a semaphore to limit the number of dialogs displayed at a time.
        Error could come from any thread so we should make sure not to meme the user with a billion dialogs.
        """
        if self.unhandled_sem.tryAcquire(n=MAX_UNHANDLED_DIALOGS):
            self.show_error_dialog("Unhandled Error", "Unhandled error occured:", exc_info)
            self.unhandled_sem.release(n=MAX_UNHANDLED_DIALOGS)

    def _excepthook(self, etype, evalue, trace):
        """
        Ensure our error is handled in the Qt event loop/main thread.
        """
        self.unhandled_exc.emit((etype, evalue, trace))

    def init_excepthook(self):
        """
        Set up an except hook so we can handle any exceptions that are not explicitly caught.
        If an exception, for example, bubbles up out of a PyQt callback it will crash the app as
        the C++ backend of PyQt has no idea to handle a Python exception (and it probably can't have any idea).
        Thus we ensure uncaught exceptions go somewhere that is still in Python land.
        """
        # Connecting this with a BlockingQueuedConnection seems to cause the app to hang on error.
        # Not sure why when the errors could come from any thread but perhaps an excepthook is a special case.
        self.unhandled_exc.connect(self._unhandled_exc)
        sys.excepthook = self._excepthook

    def set_palette_tools_enable(self, state):
        """
        Set the enable state of various palettes actions together.
        """
        self.ui.save_palette.setEnabled(state)
        self.ui.save_palette_as.setEnabled(state)
        self.ui.copy_palette.setEnabled(state)

    def launch_bbcf(self, _):
        """
        Launch BBCF via Steam.
        """
        if not steam_running():
            message = "Steam must be running in order to launch BBCF!"
            self.show_message_dialog("Steam Not Running", message)

        else:
            subprocess.call([self.paths.steam_exe, "-applaunch", BBCF_STEAM_APP_ID])

    def edit_settings(self, _):
        """
        Callback for the settings action. Display a dialog showing our app settings.
        """
        dialog = SettingsDialog(self.app_config, parent=self)
        dialog.show()

        # This will enable UI elements if we set a Steam install in the dialog.
        self._check_steam_install()

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
        self.sprite_editor.close()

    def _check_steam_install(self):
        """
        Helper to check if we have a Steam install configured and should enable relevant UI elements.
        """
        enabled = bool(self.app_config["bbsed"]["steam_install"])
        self.sprite_editor.set_selection_enable(enabled)

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

        is_nameless = PALETTE_SAVE_MARKER not in hpl_file
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
                _, character = self.sprite_editor.get_character()
                palette_id, _ = self.sprite_editor.get_palette()

                # Update the save slots to include the newly imported files, but only if we have imported
                # palettes for the current selected character and palette ID.
                self.sprite_editor.import_palette_data(character, palette_id, hpl_to_import, pac_to_import)
                self.sprite_editor.refresh()

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
        dialog = SelectDialog(self.paths, multi_select=True, parent=self)
        dialog.selection_made.connect(self._export_palettes)
        dialog.show()

    def _export_palettes(self, files_to_export):
        """
        Callback for when the SelectDialog is accepted.
        Necessary for running this dialog non-modal.
        """
        pac_path = self._choose_export_pac()

        if pac_path:
            thread = ExportThread(pac_path, files_to_export, self.paths)
            self.run_work_thread(thread, "Palette Exporter", "Exporting Palette Data...")

        else:
            self.show_message_dialog("Export Aborted", "Export path not chosen! Aborting palette export!")

    def apply_palettes(self, _):
        """
        Callback for the Apply All action. Apply all palettes to the BBCF game data.
        """
        applied_diff = self.applied_config.copy()
        dialog = SelectDialog(self.paths, config=self.select_config, diff_config=applied_diff, parent=self)
        dialog.selection_made.connect(self._apply_palettes)
        dialog.show()

    def _apply_palettes(self, files_to_apply):
        """
        Callback for when the SelectDialog is accepted.
        Necessary for running this dialog non-modal.
        """
        message = "Do you wish to apply the selected palettes to the BBCF game files?"
        confirmed = self.show_confirm_dialog("Apply Palette Confirmation", message)

        if confirmed:
            thread = ApplyThread(files_to_apply, self.paths)
            success = self.run_work_thread(thread, "Sprite Updater", "Applying Sprite Data...")

            # If the palette application succeeds we should update our applied palettes saved config
            # to match that of the palette selections config.
            if success:
                self.applied_config.load_from(self.select_config)
                self.applied_config.save()

    def discard_palette(self, _):
        """
        Discard the any edited palette files.
        """
        character_name, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()
        slot_name, _ = self.sprite_editor.get_slot()

        message = f"Do you wish to discard edits for {character_name} palette {palette_id}?"
        discard = self.show_confirm_dialog("Discard Edited Palette", message)

        if discard:
            edit_file_list = self.paths.get_edit_palette(character, palette_id, slot_name)

            for hpl_full_path in edit_file_list:
                os.remove(hpl_full_path)

            self._set_window_title(character_name, palette_id, slot_name=slot_name)
            self.ui.discard_palette.setEnabled(False)

            self.sprite_editor.refresh()

    def _restore_character_palettes(self, character):
        """
        Helper to delete the existing PAC palette file and replace it with the backed version from the game data.
        """
        pac_palette_name = GAME_PALETTE_FILE_FMT.format(character)
        pac_palette_path = os.path.join(self.paths.bbcf_data_dir, pac_palette_name)

        backup_palette_name = pac_palette_name.replace(GAME_PALETTE_EXT, BACKUP_GAME_PALETTE_EXT)
        backup_palette_path = os.path.join(self.paths.bbcf_data_dir, backup_palette_name)

        # If a backup does not exist then we should not attempt restore as we legitimately can't do it.
        if not os.path.exists(backup_palette_path):
            return

        os.remove(pac_palette_path)
        shutil.copyfile(backup_palette_path, pac_palette_path)

    def restore_all(self, _):
        """
        Restore all character palettes from the backed up game data in the BBCF install directory.
        We also reset the applied saved config values for all characters.
        """
        message = "Do you wish to restore all game files to the original versions?"
        restore = self.show_confirm_dialog("Restore Game Files", message)

        if restore:
            for character in VALID_CHARACTERS:
                self._restore_character_palettes(character)

            for section, setting, _ in self.applied_config:
                self.applied_config[section][setting] = SLOT_NAME_BBCF

    def restore_character(self, _):
        """
        Restore the selected character palettes from the backed up game data in the BBCF install directory.
        We also reset the applied saved config values for the restored character.
        """
        character_name, character = self.sprite_editor.get_character()

        message = f"Do you wish to restore game files for {character_name} to the original versions?"
        restore = self.show_confirm_dialog("Restore Game Files", message)

        if restore:
            self._restore_character_palettes(character)

            for section, setting, _ in self.applied_config:
                if section == character:
                    self.applied_config[section][setting] = SLOT_NAME_BBCF

    def _get_palette_files(self, character, palette_id, slot_name):
        """
        Get a list of files that we either want to save, copy, or paste.
        We prioritize any active edits and if no edit files exist we fall back to palette saves.
        The save fallback includes the game version of the given palette.
        """
        hpl_files_list = self.paths.get_edit_palette(character, palette_id, slot_name)

        if not hpl_files_list:
            hpl_files_list = self.paths.get_saved_palette(character, palette_id, slot_name)

        return hpl_files_list

    def _save_palette(self, save_name):
        """
        Save the current palette with the given name.
        We will be able to recall and export this palette after it is saved.
        """
        character_name, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()
        slot_name, _ = self.sprite_editor.get_slot()

        save_dst_path = self.paths.get_palette_save_path(character, palette_id, save_name)
        if not os.path.exists(save_dst_path):
            os.makedirs(save_dst_path)

        files_to_save = self._get_palette_files(character, palette_id, slot_name)

        for hpl_src_path in files_to_save:
            hpl_dst_file = os.path.basename(hpl_src_path)

            # If our source file was an active edit HPL file then it will contain the slot name in the file name.
            # When we move this file to the save directory we should remove the slot name as the slot name is
            # included in the save directory path.
            if hpl_dst_file.count(".") > 1:
                hpl_dst_file = SLOT_NAME_REGEX.sub(PALETTE_EXT, hpl_dst_file)

            hpl_dst_path = os.path.join(save_dst_path, hpl_dst_file)
            shutil.copyfile(hpl_src_path, hpl_dst_path)

            # Remove any edit files if they exist.
            for edit_hpl_file in self.paths.get_edit_palette(character, palette_id, slot_name):
                os.remove(edit_hpl_file)

        self._set_window_title(character_name, palette_id, slot_name=save_name)

        # We will be switching to the newly saved palette.
        # When a save slot is selected we disable discard and enable delete.
        self.ui.discard_palette.setEnabled(False)
        self.ui.delete_palette.setEnabled(True)

        self.sprite_editor.add_save_slot(save_name)

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
        existing_saves = self.paths.get_palette_saves(character, palette_id)
        character_name, _ = self.sprite_editor.find_character(character=character)

        while True:
            flags = QtCore.Qt.WindowType.WindowTitleHint
            message = f"Choose a name for your palette ({character_name} - {palette_id}):"
            palette_name, accepted = QtWidgets.QInputDialog.getText(self, "Name Your Palette", message, flags=flags)

            # Restrict palette names to alphanumeric characters and underscore.
            # However if the dialog is not accepted we ignore this restriction as we will be discarding this data.
            if NON_ALPHANUM_REGEX.search(palette_name) is not None and accepted:
                message = "Palette names may only contain alpha-numeric characters and underscores!"
                self.show_message_dialog("Invalid Palette Name", message, QtWidgets.QMessageBox.Icon.Critical)

            # We explicitly disallow certain names (i.e. the abbreviation of installments to the series)
            # so we can use those slots as the game-data versions of the palettes.
            elif palette_name in GAME_SLOT_NAMES and accepted:
                message = "Palette name may not be any of: {}".format(", ".join(GAME_SLOT_NAMES))
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
        slot_name, slot_type = self.sprite_editor.get_slot()
        _, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()

        # If we have a saved palette selected we keep the name previously chosen.
        if slot_type == PALETTE_SAVE:
            save_name = slot_name

        # If we have the edit slot selected then we prompt the user to choose a name.
        else:
            save_name, accepted = self._choose_palette_name(character, palette_id)

            # If we did not accept the dialog then we do not want to save the palette.
            if not accepted:
                return

        self._save_palette(save_name)

    def save_palette_as(self, _):
        """
        Save the current palette to disk. We will always prompt the user for a name.
        """
        _, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()

        palette_name, accepted = self._choose_palette_name(character, palette_id)

        # If we did not accept the dialog then we do not want to save the palette.
        if not accepted:
            return

        self._save_palette(palette_name)

    def delete_palette(self, _):
        """
        Delete the current selected saved palette.
        """
        palette_id, _ = self.sprite_editor.get_palette()
        _, character = self.sprite_editor.get_character()
        save_name, _ = self.sprite_editor.get_slot()

        message = f"Do you want to delete saved palette {save_name}?"
        delete = self.show_confirm_dialog("Delete Palette", message)

        if delete:
            save_dst_path = self.paths.get_palette_save_path(character, palette_id, save_name)
            shutil.rmtree(save_dst_path)

            self.sprite_editor.delete_slot(save_name)

            # We just deleted the current palette and will be switching back to the edit slot.
            # We need to disable the delete action.
            self.ui.delete_palette.setEnabled(False)

    def copy_palette(self, _):
        """
        Copy the current selected palette to our palette clipboard.
        The clipboard is just a list of palette files we want to copy.
        """
        _, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()
        slot_name, _ = self.sprite_editor.get_slot()

        self.clipboard = self._get_palette_files(character, palette_id, slot_name)

        self.ui.paste_palette.setEnabled(True)

    def paste_palette(self, _):
        """
        Paste the palette clipboard to the current selected palette.
        If we accept the confirmation we copy the clipboard files to the edit
        slot of the
        """
        message = ("Do you wish to paste the copied palette to the current selected palette?\n"
                   "This will overwrite any active changes.")
        confirmed = self.show_confirm_dialog("Paste Palette Confirmation", message)

        if confirmed:
            _, character = self.sprite_editor.get_character()
            palette_id, palette_num = self.sprite_editor.get_palette()
            slot_name, _ = self.sprite_editor.get_slot()

            edit_palette_path = self.paths.get_edit_palette_path(character, palette_id)

            for hpl_src_path in self.clipboard:
                hpl_file = os.path.basename(hpl_src_path)

                hpl_file = PALETTE_NUM_REGEX.sub(PALETTE_NUM_REPL.format(palette_num), hpl_file)
                hpl_file = hpl_file.replace(PALETTE_EXT, SLOT_PALETTE_EXT_FMT.format(slot_name))

                hpl_dst_path = os.path.join(edit_palette_path, hpl_file)
                shutil.copyfile(hpl_src_path, hpl_dst_path)

            # We are applying changes to a palette. Make sure the UI is updated accordingly.
            self.update_ui_for_palette()
            self.sprite_editor.refresh()

    def _update_edit_state(self, character, palette_id, slot_name):
        """
        Helper to update the window title based on presence of active changes from the user.
        """
        self.ui.discard_palette.setEnabled(False)

        # Look for any palette files with active changes.
        is_dirty = bool(self.paths.get_edit_palette(character, palette_id, slot_name))

        # If the loaded character/palette has active changes our new window title should include the edit marker.
        if is_dirty:
            self.ui.discard_palette.setEnabled(True)

        return is_dirty

    def _set_window_title(self, *pcs, slot_name=None, show_edit_mark=False):
        """
        Remove the edit marker from the window title.
        We have either discarded our active changes or saved them.
        """
        window_title = WINDOW_TITLE_BASE
        extras_len = len(pcs)

        if extras_len not in (0, 2):
            raise ValueError("Window title extras must only be character name and palette ID!")

        if extras_len == 0 and show_edit_mark:
            raise ValueError("Cannot show edit mark when no character and palette is selected!")

        if extras_len:
            window_title += WINDOW_TITLE_EXTRA.format(*pcs)

        if slot_name in GAME_SLOT_NAMES:
            slot_name = SLOT_UNTITLED if show_edit_mark else None

        if slot_name is not None:
            window_title += WINDOW_TITLE_SLOT.format(slot_name)

        if show_edit_mark:
            window_title += WINDOW_TITLE_EDIT_MARK

        self.setWindowTitle(window_title)

    def update_ui_for_palette(self):
        """
        Callback for when the sprite editor emits `image_data_changed`.
        Also invoked when we paste a palette from the palette clipboard.
        We have UI elements that should be updated when palette data is modified.
        """
        character_name, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()

        # Get the type of slot upon which we just made changes.
        slot_name, slot_type = self.sprite_editor.get_slot()

        # Add a marker to the window that indicates the user has active changes.
        self._set_window_title(character_name, palette_id, slot_name=slot_name, show_edit_mark=True)
        self.ui.discard_palette.setEnabled(True)

    def character_changed(self, character_name, _):
        """
        Callback for the sprite editor telling the mainwindow that we changed characters.
        """
        _, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()
        slot_name, _ = self.sprite_editor.get_slot()

        self.ui.delete_palette.setEnabled(False)
        self.ui.discard_palette.setEnabled(False)
        self._set_window_title()

        # Extract the character data.
        thread = ExtractThread(character, self.paths)
        if not self.run_work_thread(thread, "Sprite Extractor", "Extracting Sprite Data..."):
            # If our extract did not succeed we de-select the character and do not load any further data.
            self.sprite_editor.reset()
            return

        # If our menus and toolbars are disabled (like it is at app launch) we should now enable it.
        # At launch it is disabled due to the fact that we will not have a selected character or palette.
        # If the user clicks any of the buttons with no character or palette selected then bad things happen.
        # Note that we set the state of the menus and toolbars together so we can just check the toolbar state
        # here to probe the enable state of both UI elements.
        if not self.ui.save_palette_as.isEnabled():
            self.set_palette_tools_enable(True)

        # Check for active changes and meta data associated to them for the palette we
        # we choose (i.e. 01) when we select a new character.
        is_dirty = self._update_edit_state(character, palette_id, slot_name)

        self._set_window_title(character_name, palette_id, slot_name=slot_name, show_edit_mark=is_dirty)
        self.sprite_editor.refresh()

    def palette_changed(self, palette_id, _):
        """
        Callback for the sprite editor telling the mainwindow that we changed palettes.
        """
        character_name, character = self.sprite_editor.get_character()
        slot_name, _ = self.sprite_editor.get_slot()

        is_dirty = self._update_edit_state(character, palette_id, slot_name)

        self._set_window_title(character_name, palette_id, slot_name=slot_name, show_edit_mark=is_dirty)

        # Disable delete while we do not have a selected saved palette.
        # When we switch palettes we always default to the edit slot.
        self.ui.delete_palette.setEnabled(False)

    def palette_slot_changed(self, slot_name, slot_type):
        """
        Callback for the sprite editor telling the mainwindow that we changed palette slots.
        """
        character_name, character = self.sprite_editor.get_character()
        palette_id, _ = self.sprite_editor.get_palette()

        can_delete = (slot_type == PALETTE_SAVE)
        self.ui.delete_palette.setEnabled(can_delete)

        is_dirty = self._update_edit_state(character, palette_id, slot_name)

        self._set_window_title(character_name, palette_id, slot_name=slot_name, show_edit_mark=is_dirty)

    def show_tutorial(self):
        """
        Bring up the in-app tutorial dialog so users can learn how to use the tool.
        """
        dialog = TutorialDialog(self)
        dialog.show()

    def show_about_dialog(self):
        """
        Some some basic information about BBCF Sprite Editor.
        """
        dialog = AboutDialog(parent=self)
        dialog.exec_()

    def show_confirm_dialog(self, title, message):
        """
        Ask the user to confirm an operation.
        We set the default button to No so it is more difficult to accidentally accept the dialog.
        Return a bool indicating if the dialog was accepted or rejected.
        """
        contents_icon = QtWidgets.QMessageBox.Icon.NoIcon

        message_box = QtWidgets.QMessageBox(contents_icon, title, message, parent=self)
        message_box.setWindowIcon(Qt.QIcon(":/images/images/question.ico"))
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)

        # The return value for the `exec_()` method on a QMessageBox is the button type enum of the clicked button.
        # Note that if the user exits the dialog with the escape key that we will still return `False`.
        return message_box.exec_() == QtWidgets.QMessageBox.Yes

    def show_message_dialog(self, title, message, icon=None):
        """
        Show a message to the user.
        """
        contents_icon = QtWidgets.QMessageBox.Icon.NoIcon

        if icon is None:
            icon = Qt.QIcon(":/images/images/question.ico")
        else:
            icon = Qt.QIcon(f":/images/images/{icon}.ico")

        message_box = QtWidgets.QMessageBox(contents_icon, title, message, parent=self)
        message_box.setWindowIcon(icon)
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
