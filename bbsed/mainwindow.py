import io
import os
import traceback

from collections import defaultdict

from PyQt5 import Qt, QtCore, QtWidgets

from libpac import extract_pac
from libhip import extract_img
from libhpl import replace_palette

from .ui.mainwindow_ui import Ui_MainWindow
from .config import Configuration
from .char_info import *

PALETTE_FILE_FMT = "char_{}_pal.pac"
IMAGE_FILE_FMT = "char_{}_img.pac"


def get_data_dir():
    # TODO: this assumes Windows for now...
    data_dir = os.path.join(os.environ["APPDATA"], "bbsed")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return data_dir


class ExtractThread(QtCore.QThread):

    message = QtCore.pyqtSignal(str)

    def __init__(self, bbcf_install, data_dir, abbreviation):
        QtCore.QThread.__init__(self)
        self.abbreviation = abbreviation
        self.bbcf_install = bbcf_install
        self.data_dir = data_dir

        self.hip_images = []
        self.palette_info = defaultdict(list)

    def run(self):
        palette_cache_path = os.path.join(self.data_dir, self.abbreviation, "pal")
        image_cache_path = os.path.join(self.data_dir, self.abbreviation, "img")

        # TODO: we should probably do a more robust check than this... what if palette files are missing?
        if not os.path.exists(palette_cache_path):
            os.makedirs(palette_cache_path)

            pac_file_name = PALETTE_FILE_FMT.format(self.abbreviation)
            pac_file_path = os.path.join(self.bbcf_install, "data", "Char", pac_file_name)

            try:
                self.message.emit("Extracting palette files...")
                extract_pac(pac_file_path, palette_cache_path)

            # FIXME: LOL
            except Exception:
                traceback.print_exc()
                return

        # FIXME: add useful comment here
        for hpl_file in os.listdir(palette_cache_path):
            palette_num = hpl_file[2:4]
            palette_num_in_game = int(palette_num) + 1
            palette_id = f"{palette_num_in_game:02}"
            self.palette_info[palette_id].append(hpl_file)

        # TODO: we should probably do a more robust check than this... what if image files are missing?
        if not os.path.exists(image_cache_path):
            os.makedirs(image_cache_path)

            img_file_name = IMAGE_FILE_FMT.format(self.abbreviation)
            img_file_path = os.path.join(self.bbcf_install, "data", "Char", img_file_name)

            try:
                self.message.emit("Extracting image files...")
                extract_pac(img_file_path, image_cache_path)

            # FIXME: LOL
            except Exception:
                traceback.print_exc()
                return

        for hip_image in os.listdir(image_cache_path):
            if hip_image.endswith(".hip"):
                self.hip_images.append(hip_image)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("BBCF Sprite Editor")

        self.data_dir = get_data_dir()
        self.config = Configuration(os.path.join(self.data_dir, "app.conf"))

        # Set our previously used BBCF install path if it exists.
        if self.config.bbcf_install:
            self.ui.bbcf_path.setText(self.config.bbcf_install)

        # Disable character select and sprite editor widgets while no BBCF install has been chosen.
        # We do not want any sort of wackness occurring that can get the app into a bad state.
        else:
            self.ui.char_select.setEnabled(False)
            self.ui.sprite_group.setEnabled(False)

        self.current_char = ""
        self.current_sprite = io.BytesIO()
        self.hip_images = []
        self.palette_info = {}

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

        self.ui.select_path.clicked.connect(self.select_bbcf_install)
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

    def select_bbcf_install(self):
        """
        Select the BBCF installation location to be used by the app.
        """
        bbcf_install = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select BBCF installation location",
        )

        # If we cancelled the dialog we do not want to save anything.
        if bbcf_install:
            # Save our BBCF install path to our config.
            self.config.update(bbcf_install=bbcf_install)
            self.ui.bbcf_path.setText(bbcf_install)

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
        palette_id = self.ui.palette_select.itemText(palette_index)
        hpl_files = self.palette_info[palette_id]

        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")

        # FIXME: how do we determine which file is for what? e.g. izayoi phorizor?
        #        for now just assume that the first palette is the one that matters, as that is true frequently.
        first_palette = hpl_files[0]
        palette_full_path = os.path.join(palette_cache_path, first_palette)

        # We are only updating the
        replace_palette(self.current_sprite, palette_full_path)

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(self.current_sprite.getvalue(), "PNG")

        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        self.sprite_scene.addPixmap(png_pixmap)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

    def select_sprite(self):
        """
        A new sprite has been selected.
        Update our image preview with the new sprite.
        """
        item = self.ui.file_list.currentItem()
        hip_file = item.text()

        img_cache_dir = os.path.join(self.data_dir, self.current_char, "img")

        hip_full_path = os.path.join(img_cache_dir, hip_file)
        png_full_path = os.path.join(img_cache_dir, hip_file.replace(".hip", ".png"))

        # If we have not cached a PNG of the sprite we should do so now.
        if not os.path.exists(png_full_path):
            try:
                extract_img(hip_full_path, png_full_path)

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

        _, abbreviation = CHARACTER_INFO[char_id]
        self.current_char = abbreviation

        # Create a busy-progress-bar dialog box so the user knows the app is doing something.
        # We set the window flags to remove buttons and the like so the user cannot close it.
        # Maybe this is a bad idea in the case of error conditions but we should not get stuck
        # due to how we set up our signals in a bit.
        flags = QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint
        # Set the label, min and max progress value (max of 0 is how we get a busy-bar), dialog parent, and flags.
        dialog = QtWidgets.QProgressDialog("Extracting Sprite Data...", "", 0, 0, parent=self, flags=flags)
        dialog.setWindowTitle("Sprite Extractor")
        # Remove the cancel button. This dialog cancels itself (sortof).
        dialog.setCancelButton(None)

        def _set_message(_message):
            dialog.setLabelText(_message)

        # Run the extraction in a thread so the UI does not become unresponsive for the duration of the operation.
        thread = ExtractThread(self.config.bbcf_install, self.data_dir, abbreviation)
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
