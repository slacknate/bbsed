import io
import os
import shutil
import traceback
import subprocess

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import convert_to_hpl, replace_palette, get_palette_index

from .ui.mainwindow_ui import Ui_MainWindow
from .palettedialog import PaletteDialog
from .zoomdialog import ZoomDialog
from .config import Configuration
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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("BBCF Sprite Editor")

        self.data_dir = get_data_dir()
        self.config = Configuration(os.path.join(self.data_dir, "app.conf"))

        # Set our previously used BBCF install path if it exists.
        if self.config.steam_install:
            self.ui.steam_path.setText(self.config.steam_install)

        # Disable character select and sprite editor widgets while no BBCF install has been chosen.
        # We do not want any sort of wackness occurring that can get the app into a bad state.
        else:
            self.ui.char_select.setEnabled(False)
            self.ui.sprite_group.setEnabled(False)

        self.current_char = ""
        self.current_sprite = io.BytesIO()
        self.hip_images = []
        self.palette_info = {}

        self.palette_dialog = PaletteDialog()
        self.palette_dialog.palette_data_changed.connect(self.update_palette)

        self.zoom_dialog = ZoomDialog()

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        self.ui.select_steam.clicked.connect(self.select_steam_install)
        self.ui.file_list.itemSelectionChanged.connect(self.select_sprite)
        self.ui.palette_select.currentIndexChanged[int].connect(self.select_palette)

        # We need to sort the character info before adding to the selection combo box.
        # This way the combo box index will match the defined character IDs in the char_info module.
        sorted_chars = list(CHARACTER_INFO.items())
        sorted_chars.sort(key=lambda item: item[0])

        for char_id, (char_name, _) in sorted_chars:
            self.ui.char_select.addItem(char_name)

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
        Ensure we hide our palette dialog when we close the main window or the app won't actually close.
        Unsure if calling the superclass closeEvent is required but we do so in case it is.
        """
        QtWidgets.QMainWindow.closeEvent(self, evt)
        self.palette_dialog.hide()
        self.zoom_dialog.hide()

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

    def apply_all(self, _):
        """
        Callback for the Apply All action. Apply all palettes to the BBCF game data.
        """
        files_to_apply = {}

        for character in os.listdir(self.data_dir):
            # The app config file lives in this directory, we should ignore it.
            if character not in ("app.conf",):
                palette_cache_path = os.path.join(self.data_dir, character, "pal")
                palette_file_name = PALETTE_FILE_FMT.format(character)
                self._get_character_files(files_to_apply, palette_cache_path, palette_file_name)

        bbcf_install = os.path.join(self.config.steam_install, "steamapps", "common", "BlazBlue Centralfiction")
        self.run_work_thread(ApplyThread, "Applying Sprite Data...", "Sprite Updater", bbcf_install, files_to_apply)

    def apply_character(self, _):
        """
        Callback for the Apply Character action. Apply all palettes for selected character to the BBCF game data.
        """
        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
        files_to_apply = {}

        palette_file_name = PALETTE_FILE_FMT.format(self.current_char)
        self._get_character_files(files_to_apply, palette_cache_path, palette_file_name)

        bbcf_install = os.path.join(self.config.steam_install, "steamapps", "common", "BlazBlue Centralfiction")
        self.run_work_thread(ApplyThread, "Applying Sprite Data...", "Sprite Updater", bbcf_install, files_to_apply)

    def apply_palette(self, _):
        """
        Callback for the Apply Character action. Apply current palette for selected character to the BBCF game data.
        """
        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
        palette_id = self.ui.palette_select.currentText()
        files_to_apply = {}

        palette_num_in_files = int(palette_id) - 1
        hpl_file_prefix = f"{self.current_char}{palette_num_in_files:02}_"

        hpl_file_list = []
        palette_file_name = PALETTE_FILE_FMT.format(self.current_char)
        files_to_apply[palette_file_name] = hpl_file_list

        # We have to create a PAC file with all our HPL files in order to edit character data in a valid way.
        # However we need to ensure not to include duplicates (i.e. dirty and non-dirty versions of the same palette).
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

        bbcf_install = os.path.join(self.config.steam_install, "steamapps", "common", "BlazBlue Centralfiction")
        self.run_work_thread(ApplyThread, "Applying Sprite Data...", "Sprite Updater", bbcf_install, files_to_apply)

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
        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
        self._delete_character_files(palette_cache_path)

        pal_index = self.ui.palette_select.currentIndex()
        self._update_sprite_preview(pal_index)

    def discard_palette(self, _):
        """
        Discard the dirty version of all files associated to the current palette.
        """
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
        for character in os.listdir(self.data_dir):
            # The app config file lives in this directory, we should ignore it.
            if character not in ("app.conf",):
                palette_cache_path = os.path.join(self.data_dir, character, "pal")
                self._reset_character_files(palette_cache_path)

    def reset_character(self, _):
        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")
        self._reset_character_files(palette_cache_path)

        pal_index = self.ui.palette_select.currentIndex()
        self._update_sprite_preview(pal_index)

    def reset_palette(self, _):
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
        bbcf_install = os.path.join(self.config.steam_install, "steamapps", "common", "BlazBlue Centralfiction")

        backup_palette_name = BACKUP_PALETTE_FILE_FMT.format(character)
        backup_palette_path = os.path.join(bbcf_install, "data", "Char", backup_palette_name)

        pac_palette_name = PALETTE_FILE_FMT.format(character)
        pac_palette_path = os.path.join(bbcf_install, "data", "Char", pac_palette_name)

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
            if not self.ui.char_select.isEnabled():
                self.ui.char_select.setEnabled(True)

            # Enable the sprite preview if it is not already.
            if not self.ui.sprite_group.isEnabled():
                self.ui.sprite_group.setEnabled(True)

    def _update_sprite_preview(self, palette_index):
        """
        Update the sprite preview with the given palette index.
        This method is only invoked when we pick a new sprite or select a new palette.
        Our cached sprite uses a palette from the sprite data definition, NOT from the
        in-game palette data. This means that we should always be re-writing the palette.
        """
        # Show our palette dialog if we need to.
        if self.palette_dialog.isHidden():
            self.palette_dialog.show()

        # Show our zoom dialog if we need to.
        if self.zoom_dialog.isHidden():
            self.zoom_dialog.show()

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

        # Update the dialog palette data since we have switched palettes.
        # NOTE: When the dialog emits palette_data_changed... we end up here... we should change that eventually.
        self.palette_dialog.set_palette(palette_full_path)

        # We are only updating the palette data we aren't writing out any pixel information.
        replace_palette(self.current_sprite, palette_full_path)

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(self.current_sprite.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        self.sprite_scene.addPixmap(png_pixmap)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

        # Update the zoom dialog to the current sprite
        self.zoom_dialog.set_sprite(self.current_sprite)

    def move_zoom_cursor(self, evt):
        x = evt.x()
        y = evt.y()

        mapped_point = self.ui.sprite_preview.mapToScene(Qt.QPoint(x, y))
        self.zoom_dialog.move_cursor(mapped_point)

    def set_palette_color(self, evt):
        x = evt.x()
        y = evt.y()

        mapped_point = self.ui.sprite_preview.mapToScene(Qt.QPoint(x, y))
        palette_index = get_palette_index(self.current_sprite, (mapped_point.x(), mapped_point.y()))

        self.palette_dialog.set_palette_index(palette_index)

    def set_cross_cursor(self, _):
        self.ui.sprite_preview.viewport().setCursor(QtCore.Qt.CursorShape.CrossCursor)

    def update_palette(self):
        """
        The color in a palette has been changed by the user. Save the changes to disk.
        """
        palette_id = self.ui.palette_select.currentText()
        hpl_files = self.palette_info[palette_id]

        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")

        # FIXME: see other FIXME about HPL files
        first_palette = hpl_files[0]

        # Save our changes in a "dirty" file so we can discard them easily if we want.
        palette_full_path = os.path.join(palette_cache_path, first_palette.replace(PALETTE_EXT, DIRTY_PALETTE_EXT))

        try:
            convert_to_hpl(self.palette_dialog.get_palette_img(), palette_full_path)

        # FIXME: LOL
        except Exception:
            traceback.print_exc()
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
        png_full_path = os.path.join(img_cache_dir, hip_file.replace(SPRITE_EXT, PNG_EXT))

        # If we have not cached a PNG of the sprite we should do so now.
        if not os.path.exists(png_full_path):
            try:
                convert_from_hip(hip_full_path, png_full_path)

            # FIXME: LOL
            except Exception:
                traceback.print_exc()
                return

        # Load the sprite into memory from cache.
        self.current_sprite = io.BytesIO()
        with open(png_full_path, "rb") as png_fp:
            self.current_sprite.write(png_fp.read())

        # If no palette is selected (i.e. we are picking a sprite right after picking a character)
        # then we automatically pick the first color palette as it is the cannon palette for the character,
        pal_index = self.ui.palette_select.currentIndex()
        if pal_index == -1:
            self.ui.palette_select.setCurrentIndex(0)

        # Otherwise just update the preview to whatever palette we have selected.
        else:
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

    def character_selected(self, char_id):
        """
        A new character was picked from the character combobox.
        """
        # Don't allow the user to interact with these parts of the UI while we are updating them.
        self.ui.sprite_group.setEnabled(False)

        # Hide the palette and zoom dialogs while no palette is selected.
        self.palette_dialog.hide()
        self.zoom_dialog.hide()

        _, abbreviation = CHARACTER_INFO[char_id]
        self.current_char = abbreviation

        # Extract character data.
        bbcf_install = os.path.join(self.config.steam_install, "steamapps", "common", "BlazBlue Centralfiction")
        thread = self.run_work_thread(ExtractThread, "Extracting Sprite Data...", "Sprite Extractor",
                                      bbcf_install, self.data_dir, abbreviation)

        # Store the meta data our thread so kindly gathered for us.
        self.hip_images = thread.hip_images
        self.palette_info = thread.palette_info

        # Reset our HIP file list and add the new HIP files so we only have the currently selected character files.
        self.ui.file_list.clear()
        self.ui.file_list.addItems(self.hip_images)

        # Block signals while we add items so the signals are not emitted.
        # We do not want to try to select a palette before a sprite is selected, and
        # at the very least we do not want to spam the signals in a loop regardless.
        self.ui.palette_select.blockSignals(True)
        for palette_id, _ in self.palette_info.items():
            self.ui.palette_select.addItem(palette_id)

        # Do not select a palette while no sprites are selected.
        self.ui.palette_select.setCurrentIndex(-1)

        # Re-enable signals on palette select so it works as expected for the user.
        self.ui.palette_select.blockSignals(False)
        # Re-enable user interaction for everything else.
        self.ui.sprite_group.setEnabled(True)

    def run_work_thread(self, thread_factory, initial_message, title, *args, **kwargs):
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

        # Run the extraction in a thread so the UI does not become unresponsive for the duration of the operation.
        thread = thread_factory(*args, **kwargs)
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

        return thread
