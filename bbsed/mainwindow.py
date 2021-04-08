import io
import os
import sys
import shutil
import subprocess

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import convert_to_hpl, replace_palette, get_palette_index

from .ui.mainwindow_ui import Ui_MainWindow
from .palettedialog import PaletteDialog
from .zoomdialog import ZoomDialog
from .errordialog import ErrorDialog
from .config import Configuration
from .importer import ImportThread
from .extract import ExtractThread
from .apply import ApplyThread
from .char_info import *
from .util import *


def get_data_dir():
    # TODO: this assumes Windows for now...
    data_dir = os.path.join(os.environ["APPDATA"], "bbsed")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return data_dir


# TODO: icons
# TODO: implement a help menu with About and Tutorial entries.
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("BBCF Sprite Editor")

        self.data_dir = get_data_dir()
        self.config = Configuration(os.path.join(self.data_dir, "app.conf"))

        # Set our previously used Steam install path if it exists.
        # If we have an install we should enable relevant UI elements.
        if self.config.steam_install:
            self.ui.steam_path.setText(self.config.steam_install)
            self.ui.character_box.setEnabled(True)
            self.ui.sprite_group.setEnabled(True)

        self.current_char = ""
        self.current_sprite = io.BytesIO()
        self.hip_images = []
        self.palette_info = {}

        self.palette_dialog = PaletteDialog(self)
        self.palette_dialog.palette_data_changed.connect(self.update_palette)
        self.zoom_dialog = ZoomDialog(self)

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        self.ui.select_steam.clicked.connect(self.select_steam_install)
        # FIXME: there's something weird about drag select being off by one...
        self.ui.file_list.itemSelectionChanged.connect(self.select_sprite)
        self.ui.palette_select.currentIndexChanged[int].connect(self.select_palette)

        # We need to sort the character info before adding to the selection combo box.
        # This way the combo box index will match the defined character IDs in the char_info module.
        sorted_chars = list(CHARACTER_INFO.items())
        sorted_chars.sort(key=lambda item: item[0])

        for char_id, (char_name, _) in sorted_chars:
            self.ui.char_select.addItem(char_name, char_id)

        self.ui.char_select.setCurrentIndex(-1)
        self.ui.char_select.currentIndexChanged[int].connect(self.character_selected)

        # Set out the sprite preview mouse events so we can update various app visuals.
        self.ui.sprite_preview.setMouseTracking(True)
        self.ui.sprite_preview.mouseDoubleClickEvent = self.set_palette_color
        self.ui.sprite_preview.mouseMoveEvent = self.move_zoom_cursor
        self.ui.sprite_preview.enterEvent = self.set_cross_cursor

        # Setup menu and toolbar actions so they actually do stuff!
        self.ui.launch_bbcf.triggered.connect(self.launch_bbcf)
        self.ui.exit.triggered.connect(self.exit_app)
        self.ui.import_palettes.triggered.connect(self.import_palettes)
        self.ui.export_palettes.triggered.connect(self.export_palettes)
        self.ui.view_palette.triggered.connect(self.toggle_palette)
        self.ui.view_zoom.triggered.connect(self.toggle_zoom)
        self.ui.apply_all.triggered.connect(self.apply_all)
        self.ui.apply_character.triggered.connect(self.apply_character)
        self.ui.apply_palette.triggered.connect(self.apply_palette)
        self.ui.discard_all.triggered.connect(self.discard_all)
        self.ui.discard_character.triggered.connect(self.discard_character)
        self.ui.discard_palette.triggered.connect(self.discard_palette)
        self.ui.reset_all.triggered.connect(self.reset_all)
        self.ui.reset_character.triggered.connect(self.reset_character)
        self.ui.reset_palette.triggered.connect(self.reset_palette)
        self.ui.restore_all.triggered.connect(self.restore_all)
        self.ui.restore_character.triggered.connect(self.restore_character)
        self.ui.clear_entire_cache.triggered.connect(self.clear_entire_cache)
        self.ui.clear_character_cache.triggered.connect(self.clear_character_cache)
        self.ui.clear_palette_cache.triggered.connect(self.clear_palette_cache)

    @property
    def bbcf_install(self):
        """
        Helper property to get our BBCF install location based on our configured Steam install location.
        """
        return os.path.join(self.config.steam_install, "steamapps", "common", "BlazBlue Centralfiction")

    def launch_bbcf(self, _):
        """
        Launch BBCF via Steam.
        """
        steam_exe_path = os.path.join(self.config.steam_install, "steam.exe")
        subprocess.call([steam_exe_path, "-applaunch", BBCF_STEAM_APP_ID])

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

    def import_palettes(self, _):
        """
        Callback for the palette import action. Allow the user to import palettes they may have
        created prior to using this tool or palettes they received from friends :D
        """
        hpl_file_list = []
        pac_file_list = []

        palette_file_list, _ = QtWidgets.QFileDialog.getOpenFileNames(

            parent=self,
            caption="Select Steam installation location",
            filter="BBCF palettes (*.hpl; *.pac);;HPL files (*.hpl);;PAC files (*.pac)"
        )

        # NOTE: if we cancel the dialog then `palette_file_list` will be empty.

        for palette_full_path in palette_file_list:
            if palette_full_path.endswith(PALETTE_EXT):
                hpl_file_list.append(palette_full_path)

            elif palette_full_path.endswith(GAME_PALETTE_EXT):
                pac_file_list.append(palette_full_path)

        # Don't run any thread's if we do not need to.
        if hpl_file_list or pac_file_list:
            thread = ImportThread(hpl_file_list, pac_file_list, self.data_dir)
            self.run_work_thread(thread, "Palette Importer", "Validating palette files...")

            char_index = self.ui.char_select.currentIndex()
            pal_index = self.ui.palette_select.currentIndex()

            # If we have a selected character and palette then we should update the sprite preview
            # on the off chance that one of the imported palettes corresponds to the character and
            # palette that we are currently viewing.
            if char_index != -1 and pal_index != -1:
                self._update_sprite_preview(pal_index)

    def export_palettes(self):
        """
        Callback for the palette export action. Allow for sharing palettes with friends :D
        """
        self.show_message_dialog("Feature Not Implemented",
                                 "Export is not yet implemented! Coming soon!",
                                 QtWidgets.QMessageBox.Icon.Warning)

    def toggle_palette(self, check_state):
        """
        Callback for our palette toggle action. Set the visibility state of the palette dialog.
        Mostly useful for recovering the dialog if it was closed, but maybe some folks wanna hide it anyway.
        # TODO: can we make this state a setting and have it always hidden for people that want it that way?
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
        # TODO: can we make this state a setting and have it always hidden for people that want it that way?
        """
        self.zoom_dialog.setVisible(check_state)

    def set_zoom_visibility(self, is_visible):
        """
        Show or hide the zoom dialog and update the view zoom action check state to match.
        """
        self.zoom_dialog.setVisible(is_visible)
        self.ui.view_zoom.setChecked(is_visible)

    @staticmethod
    def _get_character_files(files_to_apply, palette_cache_path, palette_file_name):
        """
        Helper to get all palette files associated to a character.
        """
        hpl_file_list = []
        files_to_apply[palette_file_name] = hpl_file_list

        for hpl_file in os.listdir(palette_cache_path):
            hpl_full_path = os.path.join(palette_cache_path, hpl_file)

            dirty = hpl_file.endswith(DIRTY_PALETTE_EXT)
            backup = hpl_file.endswith(BACKUP_PALETTE_EXT)
            dirty_exists = os.path.exists(hpl_full_path.replace(PALETTE_EXT, DIRTY_PALETTE_EXT))

            if (dirty or (not dirty and not dirty_exists)) and not backup:
                hpl_file_list.append(hpl_full_path)

    def _run_apply_thread(self, files_to_apply):
        """
        Helper to run our apply thread based on a set of files to apply that was generated
        in the various apply button UI callbacks.
        """
        thread = ApplyThread(self.bbcf_install, files_to_apply)

        self.run_work_thread(thread, "Sprite Updater", "Applying Sprite Data...")

    def apply_all(self, _):
        """
        Callback for the Apply All action. Apply all palettes to the BBCF game data.
        """
        message = "Do you want to apply all palettes to BBCF game data?"
        apply = self.show_confirm_dialog("Apply All Palettes", message)

        if apply:
            files_to_apply = {}

            for character in os.listdir(self.data_dir):
                # The app config file lives in this directory, we should ignore it.
                if character not in ("app.conf",):
                    palette_cache_path = os.path.join(self.data_dir, character, "pal")
                    palette_file_name = PALETTE_FILE_FMT.format(character)
                    self._get_character_files(files_to_apply, palette_cache_path, palette_file_name)

            self._run_apply_thread(files_to_apply)

    def apply_character(self, _):
        """
        Callback for the Apply Character action. Apply all palettes for selected character to the BBCF game data.
        """
        character_name = self.ui.char_select.currentText()

        message = f"Do you want to apply all palettes for {character_name} to BBCF game data?"
        apply = self.show_confirm_dialog("Apply Character Palettes", message)

        if apply:
            palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
            files_to_apply = {}

            palette_file_name = PALETTE_FILE_FMT.format(self.current_char)
            self._get_character_files(files_to_apply, palette_cache_path, palette_file_name)

            self._run_apply_thread(files_to_apply)

    def apply_palette(self, _):
        """
        Callback for the Apply Character action. Apply current palette for selected character to the BBCF game data.
        """
        character_name = self.ui.char_select.currentText()
        palette_id = self.ui.palette_select.currentText()

        message = f"Do you want to apply {character_name} palette {palette_id} to BBCF game data?"
        apply = self.show_confirm_dialog("Apply Character Palettes", message)

        if apply:
            palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
            palette_id = self.ui.palette_select.currentText()
            files_to_apply = {}

            palette_num_in_files = int(palette_id) - 1
            hpl_file_prefix = f"{self.current_char}{palette_num_in_files:02}_"

            hpl_file_list = []
            palette_file_name = PALETTE_FILE_FMT.format(self.current_char)
            files_to_apply[palette_file_name] = hpl_file_list

            # We have to create a PAC file with all our HPL files in order to edit character data in a valid way.
            # However we need to ensure not to include both the dirty and non-dirty versions of the palette.
            # We only want to look for dirty versions of files associated to the current palette.
            for hpl_file in os.listdir(palette_cache_path):
                hpl_full_path = os.path.join(palette_cache_path, hpl_file)

                current = hpl_file.startswith(hpl_file_prefix)
                dirty = hpl_file.endswith(DIRTY_PALETTE_EXT)
                backup = hpl_file.endswith(BACKUP_PALETTE_EXT)

                # For palette files associated to the current palette we include the dirty versions if they exist
                # and only include non-dirty versions of the palette files if a dirty version does not exist.
                # NOTE: Right now we can only edit palette file nnXX_00.hpl as we have not yet created a mapping
                #       that defines what sprites/data the other files are associated to, so for the time being
                #       we will only ever have a dirty version of this first palette file from each PAC file.
                # We do not include backup files in application-to-game-data process.
                if current:
                    dirty_exists = os.path.exists(hpl_full_path.replace(PALETTE_EXT, DIRTY_PALETTE_EXT))

                    if (dirty or (not dirty and not dirty_exists)) and not backup:
                        hpl_file_list.append(hpl_full_path)

                # For palette files not associated to the current palette we only include the non-dirty versions.
                # We do not include backup files in application-to-game-data process.
                elif not current and not dirty and not backup:
                    hpl_file_list.append(hpl_full_path)

            self._run_apply_thread(files_to_apply)

    @staticmethod
    def _delete_character_files(palette_cache_path):
        """
        Helper to list the contents of a character palette cache and remove the dirty files from it.
        """
        for hpl_file in os.listdir(palette_cache_path):
            # Get rid of the dirty files.
            if hpl_file.endswith(DIRTY_PALETTE_EXT):
                hpl_full_path = os.path.join(palette_cache_path, hpl_file)
                os.remove(hpl_full_path)

    def discard_all(self, _):
        """
        Delete the dirty version of all palette files for all characters.
        """
        message = "Do you wish to discard all edited palettes?"
        discard = self.show_confirm_dialog("Discard All Edited Palettes", message)

        if discard:
            for character in os.listdir(self.data_dir):
                # The app config file lives in this directory, we should ignore it.
                if character not in ("app.conf",):
                    palette_cache_path = os.path.join(self.data_dir, character, "pal")
                    self._delete_character_files(palette_cache_path)

            pal_index = self.ui.palette_select.currentIndex()
            self._update_sprite_preview(pal_index)

    def discard_character(self, _):
        """
        Discard the dirty version of all palette files for the selected character.
        """
        character_name = self.ui.char_select.currentText()

        message = f"Do you wish to discard all edited palettes for {character_name}?"
        discard = self.show_confirm_dialog("Discard Edited Character Palettes", message)

        if discard:
            palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
            self._delete_character_files(palette_cache_path)

            pal_index = self.ui.palette_select.currentIndex()
            self._update_sprite_preview(pal_index)

    def discard_palette(self, _):
        """
        Discard the dirty version of all files associated to the current palette.
        """
        character_name = self.ui.char_select.currentText()
        palette_id = self.ui.palette_select.currentText()

        message = f"Do you wish to discard edits for {character_name} palette {palette_id}?"
        discard = self.show_confirm_dialog("Discard Edited Palette", message)

        if discard:
            palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
            palette_id = self.ui.palette_select.currentText()

            palette_num_in_files = int(palette_id) - 1
            hpl_file_prefix = f"{self.current_char}{palette_num_in_files:02}_"

            for hpl_file in os.listdir(palette_cache_path):
                current = hpl_file.startswith(hpl_file_prefix)
                dirty = hpl_file.endswith(DIRTY_PALETTE_EXT)

                if current and dirty:
                    hpl_full_path = os.path.join(palette_cache_path, hpl_file)
                    os.remove(hpl_full_path)

            pal_index = self.ui.palette_select.currentIndex()
            self._update_sprite_preview(pal_index)

    @staticmethod
    def _reset_character_files(palette_cache_path):
        """
        Helper to list the files in a character palette cache and remove all dirty files
        and restore non-dirty files to the game data backup.
        """
        for hpl_file in os.listdir(palette_cache_path):
            # Our backup files should be ignored here as we are using them to reset
            # palette data to the version that comes with the game data.
            if not hpl_file.endswith(BACKUP_PALETTE_EXT):
                dirty = hpl_file.endswith(DIRTY_PALETTE_EXT)
                hpl_full_path = os.path.join(palette_cache_path, hpl_file)

                # We can just go ahead and remove any files we encounter regardless of the dirty state.
                os.remove(hpl_full_path)

                # For non-dirty files we need to replace the HPL file with a copy of the game data backup.
                if not dirty:
                    hpl_backup_path = hpl_full_path.replace(PALETTE_EXT, BACKUP_PALETTE_EXT)
                    shutil.copyfile(hpl_backup_path, hpl_full_path)

    def reset_all(self, _):
        """
        Reset the all palettes for all characters to the versions from the game.
        """
        message = "Do you wish to reset all palettes to the original game versions?"
        reset = self.show_confirm_dialog("Reset All Palettes", message)

        if reset:
            for character in os.listdir(self.data_dir):
                # The app config file lives in this directory, we should ignore it.
                if character not in ("app.conf",):
                    palette_cache_path = os.path.join(self.data_dir, character, "pal")
                    self._reset_character_files(palette_cache_path)

    def reset_character(self, _):
        """
        Reset the all palettes for the selected character to the versions from the game.
        """
        character_name = self.ui.char_select.currentText()

        message = f"Do you wish to reset palettes for {character_name} to the original game versions?"
        reset = self.show_confirm_dialog("Reset Character Palettes", message)

        if reset:
            palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
            self._reset_character_files(palette_cache_path)

            pal_index = self.ui.palette_select.currentIndex()
            self._update_sprite_preview(pal_index)

    def reset_palette(self, _):
        """
        Reset the selected palette to the version from the game.
        """
        character_name = self.ui.char_select.currentText()
        palette_id = self.ui.palette_select.currentText()

        message = f"Do you wish to reset {character_name} palette {palette_id} to the original game version?"
        reset = self.show_confirm_dialog("Reset All Palettes", message)

        if reset:
            palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
            palette_id = self.ui.palette_select.currentText()

            palette_num_in_files = int(palette_id) - 1
            hpl_file_prefix = f"{self.current_char}{palette_num_in_files:02}_"

            for hpl_file in os.listdir(palette_cache_path):
                # Our backup files should be ignored here as we are using them to reset
                # palette data to the version that comes with the game data.
                if not hpl_file.endswith(BACKUP_PALETTE_EXT):
                    current = hpl_file.startswith(hpl_file_prefix)
                    dirty = hpl_file.endswith(DIRTY_PALETTE_EXT)

                    if current:
                        hpl_full_path = os.path.join(palette_cache_path, hpl_file)

                        # We can just go ahead and remove any files we encounter regardless of the dirty state.
                        os.remove(hpl_full_path)

                        # For non-dirty files we need to replace the HPL file with a copy of the game data backup.
                        if not dirty:
                            hpl_backup_path = hpl_full_path.replace(PALETTE_EXT, BACKUP_PALETTE_EXT)
                            shutil.copyfile(hpl_backup_path, hpl_full_path)

            pal_index = self.ui.palette_select.currentIndex()
            self._update_sprite_preview(pal_index)

    def _restore_character_palettes(self, character):
        """
        Helper to delete the existing PAC palette file and replace it with the backed version from the game data.
        """
        backup_palette_name = BACKUP_PALETTE_FILE_FMT.format(character)
        backup_palette_path = os.path.join(self.bbcf_install, "data", "Char", backup_palette_name)

        pac_palette_name = PALETTE_FILE_FMT.format(character)
        pac_palette_path = os.path.join(self.bbcf_install, "data", "Char", pac_palette_name)

        os.remove(pac_palette_path)
        shutil.copyfile(backup_palette_path, pac_palette_path)

    def restore_all(self, _):
        """
        Restore all character palettes from the backed up game data in the BBCF install directory.
        """
        for character in os.listdir(self.data_dir):
            # The app config file lives in this directory, we should ignore it.
            if character not in ("app.conf",):
                self._restore_character_palettes(character)

    def restore_character(self, _):
        """
        Restore the selected character palettes from the backed up game data in the BBCF install directory.
        """
        self._restore_character_palettes(self.current_char)

    def clear_entire_cache(self, _):
        """
        Remove all cached data.
        """
        message = "Do you wish to clear all editor cache data?"
        clear = self.show_confirm_dialog("Clear Editor Cache", message)

        if clear:
            for character in os.listdir(self.data_dir):
                # The app config file lives in this directory, we should ignore it.
                if character not in ("app.conf",):
                    character_full_path = os.path.join(self.data_dir, character)
                    shutil.rmtree(character_full_path)

            # We no longer have sprite data. We should reset the UI so the user must re-select things
            # which will subsequently cause the app to re-cache data.
            self._reset_ui(deselect_character=True)

    def clear_character_cache(self, _):
        """
        Remove all cached data for the selected character.
        """
        character_name = self.ui.char_select.currentText()

        message = f"Do you wish to clear editor cache data for {character_name}?"
        clear = self.show_confirm_dialog("Clear Editor Character Cache", message)

        if clear:
            shutil.rmtree(os.path.join(self.data_dir, self.current_char))

            # We no longer have sprite data. We should reset the UI so the user must re-select things
            # which will subsequently cause the app to re-cache data.
            self._reset_ui(deselect_character=True)

    def clear_palette_cache(self, _):
        """
        Remove all cached data for the selected palette.
        """
        character_name = self.ui.char_select.currentText()
        palette_id = self.ui.palette_select.currentText()

        message = f"Do you wish to clear editor cache data for {character_name} palette {palette_id}?"
        clear = self.show_confirm_dialog("Clear Editor Palette Cache", message)

        if clear:
            palette_num_in_files = int(palette_id) - 1
            hpl_file_prefix = f"{self.current_char}{palette_num_in_files:02}_"

            palette_cache_dir = os.path.join(self.data_dir, self.current_char, "pal")

            for hpl_file in os.listdir(palette_cache_dir):
                if hpl_file.startswith(hpl_file_prefix):
                    hpl_full_path = os.path.join(palette_cache_dir, hpl_file)
                    os.remove(hpl_full_path)

            with block_signals(self.ui.file_list):
                # Empty QModelIndex is the list widget equivalent to -1 for combo boxes.
                self.ui.file_list.setCurrentIndex(QtCore.QModelIndex())

            self._clear_sprite_data()

    def _restore_character_palettes(self, character):
        """
        Helper to delete the existing PAC palette file and replace it with the backed version from the game data.
        """
        backup_palette_name = BACKUP_PALETTE_FILE_FMT.format(character)
        backup_palette_path = os.path.join(self.bbcf_install, "data", "Char", backup_palette_name)

        pac_palette_name = PALETTE_FILE_FMT.format(character)
        pac_palette_path = os.path.join(self.bbcf_install, "data", "Char", pac_palette_name)

        os.remove(pac_palette_path)
        shutil.copyfile(backup_palette_path, pac_palette_path)

    def restore_all(self, _):
        """
        Restore all character palettes from the backed up game data in the BBCF install directory.
        """
        message = "Do you wish to restore all game files to the original versions?"
        restore = self.show_confirm_dialog("Restore Game Files", message)

        if restore:
            for character in os.listdir(self.data_dir):
                # The app config file lives in this directory, we should ignore it.
                if character not in ("app.conf",):
                    self._restore_character_palettes(character)

    def restore_character(self, _):
        """
        Restore the selected character palettes from the backed up game data in the BBCF install directory.
        """
        character_name = self.ui.char_select.currentText()

        message = f"Do you wish to restore game files for {character_name} to the original versions?"
        restore = self.show_confirm_dialog("Restore Game Files", message)

        if restore:
            self._restore_character_palettes(self.current_char)

    def select_steam_install(self):
        """
        Select the BBCF installation location to be used by the app.
        """
        steam_install = QtWidgets.QFileDialog.getExistingDirectory(

            parent=self,
            caption="Select Steam installation location",
        )

        # If we cancelled the dialog we do not want to save anything.
        if steam_install:
            # Save our Steam install path to our config.
            self.config.update(steam_install=steam_install)
            self.ui.steam_path.setText(steam_install)

            # Enable the character select if it is not already.
            if not self.ui.character_box.isEnabled():
                self.ui.character_box.setEnabled(True)

            # Enable the sprite preview if it is not already.
            if not self.ui.sprite_group.isEnabled():
                self.ui.sprite_group.setEnabled(True)

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

    def _reset_ui(self, deselect_character):
        """
        Reset the state of the UI. This includes clearing all graphics views, emptying the selectable
        sprite file list, and resetting combo box selections. We also clear meta data associated to these things.
        """
        self.hip_images = []
        self.palette_info = {}
        self.current_char = ""

        with block_signals(self.ui.palette_select):
            self.ui.palette_select.setCurrentIndex(-1)

        with block_signals(self.ui.file_list):
            self.ui.file_list.clear()

        if deselect_character:
            with block_signals(self.ui.char_select):
                self.ui.char_select.setCurrentIndex(-1)

        self._clear_sprite_data()

    def _update_sprite_preview(self, palette_index):
        """
        Update the sprite preview with the given palette index.
        This method is only invoked when we pick a new sprite or select a new palette.
        Our cached sprite uses a palette from the sprite data definition, NOT from the
        in-game palette data. This means that we should always be re-writing the palette.
        """
        palette_id = self.ui.palette_select.itemText(palette_index)
        hpl_files = self.palette_info[palette_id]

        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")

        # FIXME: how do we determine which file is for what? e.g. izayoi phorizor?
        #        for now just assume that the first palette is the one that matters, as that is true frequently.
        first_palette = hpl_files[0]

        palette_full_path = os.path.join(palette_cache_path, first_palette)
        dirty_full_path = os.path.join(palette_cache_path, first_palette.replace(PALETTE_EXT, DIRTY_PALETTE_EXT))

        # If we have made changes to a palette we should load those.
        # The "normal" HPL file is kept in sync with what exists in the game data at the BBCF install path.
        if os.path.exists(dirty_full_path):
            palette_full_path = dirty_full_path

        # If we have cleared the cache recently we may need to re-extract the palette data.
        # We will only need to perform extraction here if we have cleared a specific palette from the cache.
        # When the entire cache or a character cache is cleared we are forced to re-select a character
        # which will result in data extraction occurring before we reach this point.
        if not os.path.exists(palette_full_path):
            self._run_extract_thread()

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
        # TODO: implement an app setting and keep this hidden if the user wants.
        if self.palette_dialog.isHidden():
            self.set_palette_visibility(True)

        # Show our zoom dialog if we need to.
        # TODO: implement an app setting and keep this hidden if the user wants.
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
        hpl_files = self.palette_info[palette_id]

        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")

        # FIXME: see other FIXME about HPL files
        first_palette = hpl_files[0]

        # Save our changes in a "dirty" file so we can discard them easily if we want.
        palette_full_path = os.path.join(palette_cache_path, first_palette.replace(PALETTE_EXT, DIRTY_PALETTE_EXT))

        try:
            convert_to_hpl(self.palette_dialog.get_palette_img(), palette_full_path)

        except Exception:
            message = f"Failed to update palette {palette_id} for {character_name}!"
            self.show_error_dialog("Error Updating Palette", message)
            return

        pal_index = self.ui.palette_select.currentIndex()
        self._update_sprite_preview(pal_index)

    def select_sprite(self):
        """
        A new sprite has been selected.
        Update our image preview with the new sprite.
        """
        item = self.ui.file_list.currentItem()
        hip_file = item.text()

        img_cache_dir = os.path.join(self.data_dir, self.current_char, "img")
        hip_full_path = os.path.join(img_cache_dir, hip_file)

        try:
            self.current_sprite = io.BytesIO()
            convert_from_hip(hip_full_path, self.current_sprite)

        except Exception:
            self.show_error_dialog("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")
            return

        pal_index = self.ui.palette_select.currentIndex()
        self._update_sprite_preview(pal_index)

    def select_palette(self, index):
        """
        A new palette has been selected.
        Replace the palette of the currently selected sprite and update the image preview.
        """
        item = self.ui.file_list.currentItem()

        # Only update the preview is we have a selected sprite and we have also have a selected palette.
        if item is not None and index >= 0:
            self._update_sprite_preview(index)

    def _run_extract_thread(self):
        """
        Helper method to extract game data. Note that this procedure will only extract files
        called out in the sprite and palette PAC files that it cannot find in the cache.
        """
        thread = ExtractThread(self.bbcf_install, self.data_dir, self.current_char)

        success = self.run_work_thread(thread, "Sprite Extractor", "Extracting Sprite Data...")

        # Store the meta data our thread so kindly gathered for us.
        if success:
            self.palette_info = thread.palette_info
            self.hip_images = thread.hip_images

    def character_selected(self, char_id):
        """
        A new character was picked from the character combobox.
        """
        # Don't allow the user to interact with these parts of the UI while we are updating them.
        self.ui.sprite_group.setEnabled(False)

        # Reset all the things. This method actually has the deselect_character argument specifically
        # so we can use it here without immediately deselecting the character we just picked.
        self._reset_ui(deselect_character=False)

        # Update the current character string.
        _, self.current_char = CHARACTER_INFO[char_id]

        # Extract the character data.
        self._run_extract_thread()

        # Reset our HIP file list and add the new HIP files so we only have the currently selected character files.
        with block_signals(self.ui.file_list):
            self.ui.file_list.addItems(self.hip_images)

        # Block signals while we add items so the signals are not emitted.
        # We do not want to try to select a palette before a sprite is selected, and
        # at the very least we do not want to spam the signals in a loop regardless.
        with block_signals(self.ui.palette_select):
            for palette_id, _ in self.palette_info.items():
                self.ui.palette_select.addItem(palette_id)

            # Automatically select the first palette.
            # We intentionally select this in the block_signals block so we do not try to set
            # palette data before a sprite is selected.
            self.ui.palette_select.setCurrentIndex(0)

        # Re-enable user interaction for everything else.
        self.ui.sprite_group.setEnabled(True)
        # If our toolbar is disabled (like it is at app launch) we should now enable it.
        # At launch it is disabled due to the fact that we will not have a selected character or palette.
        # If the user clicks any of the buttons with no character or palette selected then bad things happen.
        if not self.ui.palette_toolbar.isEnabled():
            self.ui.palette_toolbar.setEnabled(True)

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
            self.show_error_dialog(*thread.error.get_details())

        # Return the success status of the thread. A thread is considered successful if no errors, exceptional
        # or otherwise, were encountered while performing the work procedure.
        return thread.error is None and thread.exc is None
