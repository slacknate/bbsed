import io
import os
import traceback

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import convert_from_hip
from libhpl import convert_to_hpl, replace_palette, get_palette_index

from .ui.mainwindow_ui import Ui_MainWindow
from .palettedialog import PaletteDialog
from .zoomdialog import ZoomDialog
from .extract import ExtractThread
from .config import Configuration
from .char_info import *


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

        self.palette_dialog = PaletteDialog()
        self.palette_dialog.palette_data_changed.connect(self.update_palette)

        self.zoom_dialog = ZoomDialog()

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

        # Set out the sprite preview mouse events so we can update various app visuals.
        self.ui.sprite_preview.setMouseTracking(True)
        self.ui.sprite_preview.mouseDoubleClickEvent = self.set_palette_color
        self.ui.sprite_preview.mouseMoveEvent = self.move_zoom_cursor
        self.ui.sprite_preview.enterEvent = self.set_cross_cursor

    def closeEvent(self, evt):
        """
        Ensure we hide our palette dialog when we close the main window or the app won't actually close.
        Unsure if calling the superclass closeEvent is required but we do so in case it is.
        """
        QtWidgets.QMainWindow.closeEvent(self, evt)
        self.palette_dialog.hide()
        self.zoom_dialog.hide()

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
        palette_id = self.ui.palette_select.currentText()
        hpl_files = self.palette_info[palette_id]

        palette_cache_path = os.path.join(self.data_dir, self.current_char, "pal")

        # FIXME: see other FIXME about HPL files
        first_palette = hpl_files[0]
        palette_full_path = os.path.join(palette_cache_path, first_palette)

        try:
            convert_to_hpl(self.palette_dialog.get_palette_img(), palette_full_path)

        # FIXME: LOL
        except Exception:
            traceback.print_exc()
            return

        index = self.ui.palette_select.currentIndex()
        self._update_sprite_preview(index)

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
