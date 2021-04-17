import io
import os

from PyQt5 import Qt, QtCore, QtWidgets

from libhip import hip_to_png
from libhpl import PNGPalette, PNGPaletteImage

from .ui.spriteeditor_ui import Ui_Editor

from .palettedialog import COLOR_BOX_SIZE, PaletteDialog
from .zoomdialog import ZoomDialog
from .crosshair import Crosshair
from .char_info_ext import *
from .char_info import *
from .util import *

CROSS_HAIR_SIZE = 20

HIP_FILE_ROLE = QtCore.Qt.ItemDataRole.UserRole

COLUMN_SPRITE_NAME = 0
COLUMN_HIP_FILE = 1

SPRITE_PREFIX_LEN = 8
EFFECT_PREFIX_LEN = 8


def get_other(two_tuple, item):
    """
    Simple boolean logic trick. The swap tuple has two items and thus a format can only
    possibly have an index of 0 or 1. If we logically invert the index of the format we
    found and convert the result back to int we get the index of the format we are swapping to.
    """
    index = two_tuple.index(item)
    other_index = int(not index)
    return two_tuple[other_index]


def get_palette_swap(swap_palettes, sprite_item):
    """
    Check if we need to swap the HPL format for this sprite item in the file list.
    We return a boolean indicating if we swapped a palette file.
    """
    swapped = False

    # Each swap is a tuple of two HPL formats.
    for swap_files in swap_palettes:
        hpl_fmt = sprite_item.hpl_fmt

        # If our item HPL format is in the swap tuple then we need to get the format
        # that is NOT the one currently associated to the item and assign it.
        if hpl_fmt in swap_files:
            sprite_item.hpl_fmt = get_other(swap_files, hpl_fmt)
            swapped = True
            break

    return swapped


class CharacterState:
    def __init__(self, sprite, sprite_editor):
        self.sprite_editor = sprite_editor
        self.character_dialog = None
        self.sprite = sprite
        self.swap_info = {}
        self.initial = None

    def _set_swap_info(self, char_states):
        """
        Create a mapping of HPL palette formats to color indices that
        need to be swapped when a state change occurs.
        """
        swap_colors = char_states[STATE_CHANGE].get(SWAP_COLORS, ())

        for color_swap_info in swap_colors:
            hpl_fmt = color_swap_info[PALETTE_FILE]
            swap_indices = color_swap_info[SWAP_INDICES]

            self.swap_info[hpl_fmt] = swap_indices

    def _show_states(self, character_name, state_name, state_choices):
        """
        Create and display a dialog for the given character that displays a character state (e.g.
        Izayoi Gain Art) and choices for the state.
        """
        dialog = QtWidgets.QDialog(flags=QtCore.Qt.WindowType.WindowTitleHint, parent=self.sprite_editor.mainwindow)
        dialog.setWindowTitle(f"{character_name} - Extra Controls")

        parent_layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(parent_layout)

        state_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setText(state_name)
        state_layout.addWidget(label)

        def _make_state_callback():
            """
            Make a function that accepts the combobox string value and uses a closure of
            the state name to pass to a sprite editor method to handle state changes.
            """
            return lambda _state_value: self.sprite_editor.character_state_change(state_name, _state_value)

        combobox = QtWidgets.QComboBox()
        combobox.addItems(state_choices)
        combobox.currentTextChanged.connect(_make_state_callback())
        state_layout.addWidget(combobox)

        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        state_layout.addItem(spacer)

        parent_layout.addLayout(state_layout)

        dialog.get_state_name = lambda: state_name
        dialog.get_state = combobox.currentText
        dialog.show()

        self.character_dialog = dialog

    def load_character(self, character_id):
        """
        Reset our character state information and determine if we have
        character state information that the user needs to be able to work with.
        """
        self.swap_info = {}
        self.initial = None

        if self.character_dialog is not None:
            self.character_dialog.hide()
            self.character_dialog = None

        character_name, _ = CHARACTER_INFO[character_id]
        ext_info = CHARACTER_EXT_INFO[character_id]
        char_states = ext_info.get(CHARACTER_STATES, {})

        # If we have defined character states then we need parse the definition
        # into actionable data that this object can use.
        if char_states:
            self.initial = char_states[STATE_INITIAL]
            state_name, state_choices = char_states[STATE_DEFINITION]

            self._set_swap_info(char_states)
            self._show_states(character_name, state_name, state_choices)

    def should_swap(self, sprite_item):
        """
        This method is used by the sprite editor in `SpriteEditor._refresh()`, and in
        that method we always reload the palette file.
        As such, we only need to swap colors if the current state choice is not the initial state as
        when the palette is reloaded the initial state is automatically displayed.
        Note that we also ensure that the given sprite item has a palette that requires a swap in the first place.
        """
        swap = False

        # Only attempt to fetch the character state if there is a state to be fetched!
        if self.character_dialog is not None:
            state = self.character_dialog.get_state()
            swap = (sprite_item.hpl_fmt in self.swap_info and state != self.initial)

        return swap

    def swap_colors(self, sprite_item):
        """
        Swap the colors of the relevant palette indices for this sprite item.
        """
        swap_indices = self.swap_info[sprite_item.hpl_fmt]
        for index1, index2 in swap_indices:
            color1, color2 = self.sprite.get_index_color_range(index1, index2)
            self.sprite.set_index_color_range((index1, color2), (index2, color1))

    def get_swap_of(self, sprite_item, index):
        """
        When we fetch the palette index of a double clicked pixel we need to
        check if that palette index is an index that has been swapped.
        We return `None` if there is no defined swap index and ensure that
        we actually had to swap in the first place before getting our swap index.
        """
        swap_index = None

        if self.should_swap(sprite_item):
            swap_indices = self.swap_info[sprite_item.hpl_fmt]

            for swap in swap_indices:
                if index in swap:
                    swap_index = get_other(swap, index)
                    break

        return swap_index

    def hide(self):
        """
        Hide the character dialog if it exists.
        We need to expose this control to the spride editor so we can close
        the dialog when we close the app if necessary.
        """
        if self.character_dialog is not None:
            self.character_dialog.hide()


class SpriteGroupItem(QtWidgets.QTreeWidgetItem):
    """
    Top level item in the sprite list to represent a group of HIP images that share an HPL palette file.
    """
    def __init__(self, name):
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.name = name

    def data(self, column, role):
        if column == COLUMN_SPRITE_NAME and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.name


class SpriteFileItem(QtWidgets.QTreeWidgetItem):
    """
    Child item in the sprite list to represent a HIP image associated to the current selected character.
    """
    def __init__(self, hip_full_path, hip_file, hpl_fmt):
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.hip_full_path = hip_full_path
        self.hip_file = hip_file
        self.hpl_fmt = hpl_fmt
        self.palette_num = ""

    @property
    def hpl_file(self):
        """
        Our HPL palette file is associated to a character and palette.
        The character abbreviation is already include in this string but
        the palette can change dynamically from the user interface.
        The palette number is updated when we call `SpriteEditor.refresh()`.
        """
        return self.hpl_fmt.format(self.palette_num)

    def data(self, column, role):
        if column == COLUMN_HIP_FILE and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.hip_file


class SpriteEditor(QtWidgets.QWidget):

    image_data_changed = QtCore.pyqtSignal()
    character_changed = QtCore.pyqtSignal(str, str)
    palette_changed = QtCore.pyqtSignal(str, str)
    palette_slot_changed = QtCore.pyqtSignal(str, int)

    def __init__(self, mainwindow, paths, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.ui = Ui_Editor()
        self.ui.setupUi(self)

        # The visualized palette of our sprite.
        self.palette = PNGPalette(COLOR_BOX_SIZE)
        # The sprite we display.
        self.sprite = PNGPaletteImage()
        # An object to manage the display of stateful characters.
        # A stateful character is a character like Izayoi where a user action can
        # change a character state (Gain Art) that in turn changes the colors displayed on the character.
        self.state = CharacterState(self.sprite, self)

        self.crosshair = Crosshair(CROSS_HAIR_SIZE, False, 0, 0)

        self.mainwindow = mainwindow
        self.paths = paths

        # We need to sort the character info before adding to the selection combo box.
        # This way the combo box index will match the defined character IDs in the char_info module.
        sorted_chars = list(CHARACTER_INFO.items())
        sorted_chars.sort(key=lambda item: item[0])

        for _, (character_name, character) in sorted_chars:
            self.ui.char_select.addItem(character_name, character)

        self.ui.char_select.setCurrentIndex(-1)
        self.ui.char_select.currentIndexChanged.connect(self.select_character)
        self.ui.palette_select.currentIndexChanged.connect(self.select_palette)
        self.ui.slot_select.currentIndexChanged.connect(self.select_palette_slot)

        # Create editor related dialogs and associate them to their respective View Menu check items.
        self.zoom_dialog = ZoomDialog(self.mainwindow.ui.view_zoom, parent=mainwindow)
        self.palette_dialog = PaletteDialog(self.mainwindow.ui.view_palette, parent=mainwindow)
        self.palette_dialog.index_selected.connect(self.choose_color_from_index)

        self.ui.sprite_list.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)
        self.ui.sprite_list.itemSelectionChanged.connect(self.select_sprite)

        # Set up the sprite preview mouse events so we can update various app visuals.
        self.ui.sprite_preview.setMouseTracking(True)
        self.ui.sprite_preview.mouseDoubleClickEvent = self.choose_color_from_coord
        self.ui.sprite_preview.mouseMoveEvent = self.mouse_move_event
        # Do not show a cursor as we are going to be manually drawing a cursor. Why?
        # I am not happy with the CrossCursor that is built into Qt, and we have to implement
        # a way to draw a crosshair for the Zoom Dialog anyway.
        self.ui.sprite_preview.viewport().setCursor(QtCore.Qt.CursorShape.BlankCursor)

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_preview.setScene(self.sprite_scene)

    def get_character(self):
        """
        Get the name and character ID of the current selected character.
        """
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()
        return character_name, character

    def find_character(self, character_name=None, character=None):
        """
        Find a character. We allow for finding a character via name or by abbreviation.
        """
        character_id = -1

        if character_name is None and character is None:
            raise ValueError("Must provide either a character name or a character abbreviation!")

        if character_name:
            character_id = self.ui.char_select.findText(character_name)

        if character:
            character_id = self.ui.char_select.findData(character)

        return CHARACTER_INFO[character_id]

    def get_palette(self):
        """
        Get the palette ID and palette number of the current selected palette.
        A palette ID is the number displayed in game, a palette number is the number used in the files on disk.
        """
        palette_id = self.ui.palette_select.currentText()
        palette_num = self.ui.palette_select.currentData()
        return palette_id, palette_num

    def get_slot(self):
        """
        Get the palette slot name and slot typeof the current selected palette slot.
        """
        slot_name = self.ui.slot_select.currentText()
        slot_type = self.ui.slot_select.currentData()
        return slot_name, slot_type

    def set_slot(self, slot_name=None, slot_type=None):
        """
        Set the current palette slot. We allow for setting by name or type.
        """
        slot_index = -1

        if slot_name is None and slot_type is None:
            raise ValueError("Must provide either a slot name or a slot type!")

        if slot_name:
            slot_index = self.ui.slot_select.findText(slot_name)

        if slot_type:
            slot_index = self.ui.slot_select.findData(slot_type)

        self.ui.slot_select.setCurrentIndex(slot_index)

    def delete_slot(self, save_name):
        """
        We have deleted the save slot identified by `save_name`. We should remove it from the UI.
        """
        save_index = self.ui.slot_select.findText(save_name)

        with block_signals(self.ui.slot_select):
            self.ui.slot_select.removeItem(save_index)

        # Re-select the edit slot after we delete a palette.
        self.ui.slot_select.setCurrentIndex(0)

    def import_palette_data(self, character, palette_id, hpl_to_import, pac_to_import):
        """
        We have successfully imported palette data. Update the UI to include the new palettes if applicable.
        """
        with block_signals(self.ui.slot_select):
            for save_char, save_pal_id, save_name in hpl_to_import.keys():
                if save_char == character and save_pal_id == palette_id:
                    self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

            for file_info in pac_to_import.values():
                for save_char, save_pal_id, save_name in file_info.keys():
                    if save_char == character and save_pal_id == palette_id:
                        self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

    def add_save_slot(self, slot_name):
        """
        We have saved a palette. Add the slot name to the UI if necessary and select the slot.
        """
        # We may be saving changes made to a palette that already has a save name.
        save_index = self.ui.slot_select.findText(slot_name)

        with block_signals(self.ui.slot_select):
            # Only add a new item if this save name is new.
            # This will happen if the palette has not been saved before
            # or if the user has selected the "Save As" option.
            if save_index < 0:
                self.ui.slot_select.addItem(slot_name, PALETTE_SAVE)
                save_index = self.ui.slot_select.findText(slot_name)

            self.ui.slot_select.setCurrentIndex(save_index)

        # If this is the first palette saved for this character and palette ID then we will need to enable
        # the save select combobox.
        if not self.ui.slot_select.isEnabled():
            self.ui.slot_select.setEnabled(True)

    def _update_save_slots(self, character_saves):
        """
        We have selected a character or a palette.
        We need to update the available slots presented in the UI.
        """
        with block_signals(self.ui.slot_select):
            # Clearing the save select and re-adding items will auto-select the first item
            # which will always be a non-saved palette.
            self.ui.slot_select.clear()
            self.ui.slot_select.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

            # Set the save select enable state based on the presence of files on disk.
            self.ui.slot_select.setEnabled(bool(character_saves))
            for save_name in character_saves:
                self.ui.slot_select.addItem(save_name, PALETTE_SAVE)

    def character_state_change(self, _, __):
        """
        Callback for stateful characters so the editor can respond to state changes
        controlled by a character "Extra Controls" dialog.
        Here we look for any palettes that we need to swap on sprite items.
        An example of sprite item palette swaps would be Izayoi's special moves; the
        slash effects change color depending on Gain Art.
        """
        should_refresh = False

        character_id = self.ui.char_select.currentIndex()
        ext_info = CHARACTER_EXT_INFO[character_id]

        char_states = ext_info[CHARACTER_STATES]
        swap_palettes = char_states[STATE_CHANGE].get(SWAP_PALETTES, ())

        for top_level_item in self._iterate_sprite_groups():
            for sprite_item in self._iterate_sprite_files(top_level_item):
                should_refresh |= get_palette_swap(swap_palettes, sprite_item)

        if should_refresh:
            self.refresh()

    def select_character(self):
        """
        A new character was picked from the character combobox.
        Note that we explicity DO NOT update the sprite list here.
        We need to wait for the mainwindow to perform sprite extraction (if necessary)
        and after that completes the mainwindow will invoke `SpriteEditor.refresh()`.
        """
        self._reset()

        character_id = self.ui.char_select.currentIndex()
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()

        # Don't allow the user to interact with these parts of the UI while we are updating them.
        self.ui.sprite_group.setEnabled(False)

        # Block signals while we add items so the signals are not emitted.
        # We do not want to try to select a palette before a sprite is selected, and
        # at the very least we do not want to spam the signals in a loop regardless.
        with block_signals(self.ui.palette_select):
            for palette_id, palette_num in iter_palettes():
                self.ui.palette_select.addItem(palette_id, palette_num)

            # Automatically select the first palette.
            # We intentionally select this in the block_signals block so we do not try to set
            # palette data before a sprite is selected.
            self.ui.palette_select.setCurrentIndex(0)

        # Get the palette ID from the widget for the sake of consistency.
        palette_id = self.ui.palette_select.currentText()

        # Update the UI to show any save slots for the first palette.
        character_saves = self.paths.get_character_saves(character, palette_id)
        self._update_save_slots(character_saves)

        # Load up the newly selected character information into our state manager.
        self.state.load_character(character_id)

        # Re-enable user interaction for everything else.
        self.ui.sprite_group.setEnabled(True)

        self.character_changed.emit(character_name, character)

    def select_palette(self):
        """
        A new palette has been selected.
        Replace the palette of the currently selected sprite and update the image preview.
        """
        character = self.ui.char_select.currentData()
        palette_id = self.ui.palette_select.currentText()
        palette_num = self.ui.palette_select.currentData()

        # When we select a palette ID we need to look for existing saved palettes associated to it.
        # Based on the presence of these files we also need to update the state of the UI.
        character_saves = self.paths.get_character_saves(character, palette_id)
        self._update_save_slots(character_saves)

        self.refresh()

        self.palette_changed.emit(palette_id, palette_num)

    def select_palette_slot(self):
        """
        We have selected a palette which has been saved by the user.
        Disable the delete button when we have the Edit slot selected.
        """
        slot_name = self.ui.slot_select.currentText()
        slot_type = self.ui.slot_select.currentData()

        self.refresh()

        self.palette_slot_changed.emit(slot_name, slot_type)

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

    def _refresh(self):
        """
        Update the sprite preview with the given palette index.
        If no index is provided we assume that the current index is to be used.
        This method is only invoked when we pick a new sprite or select a new palette.
        Our cached sprite uses a palette from the sprite data definition, NOT from the
        in-game palette data. This means that we should always be re-writing the palette.
        """
        character = self.ui.char_select.currentData()
        slot_name = self.ui.slot_select.currentText()
        slot_type = self.ui.slot_select.currentData()
        palette_id = self.ui.palette_select.currentText()

        # If we have a saved palette selected we should display that palette.
        if slot_type == PALETTE_SAVE:
            save_name = slot_name
            hpl_file_path = self.paths.get_character_save_path(character, palette_id, save_name)

        # Otherwise display the edit slot data.
        else:
            hpl_file_path = self.paths.get_edit_palette_path(character, palette_id)

        sprite_item = self.ui.sprite_list.currentItem()
        hpl_full_path = os.path.join(hpl_file_path, sprite_item.hpl_file)

        try:
            self.palette.load_hpl(hpl_full_path)
            self.sprite.load_hpl(hpl_full_path)

        except Exception:
            self.show_error_dialog("Error Setting Palette", "Failed to update the selected palette!")
            return

        # We only need to color swap if we have an active item.
        if sprite_item is not None and not isinstance(sprite_item, SpriteGroupItem):
            if self.state.should_swap(sprite_item):
                self.state.swap_colors(sprite_item)

        # ??.
        palette_image = io.BytesIO()
        self.palette.save_png(palette_image)
        palette_image = palette_image.getvalue()

        sprite_image = io.BytesIO()
        self.sprite.save_png(sprite_image)
        sprite_image = sprite_image.getvalue()
        zoom_image = io.BytesIO(sprite_image)

        png_pixmap = Qt.QPixmap()
        png_pixmap.loadFromData(sprite_image, "PNG")

        # We need a new crosshair every time we clear the scene.
        # We have updated the sprite data anyway so it makes sense to recreate it.
        self.crosshair = Crosshair(CROSS_HAIR_SIZE, True, png_pixmap.width(), png_pixmap.height())

        # Clear our image date and load in the updates image data.
        self.sprite_scene.clear()
        pixmap_item = self.sprite_scene.addPixmap(png_pixmap)
        self.sprite_scene.addItem(self.crosshair)

        # Set the parent item of the crosshair to the added png pixmap so the crosshair can
        # determine what color it should be drawn using the pixmap as a reference.
        self.crosshair.setParentItem(pixmap_item)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.sprite_preview.viewport().update()

        # Update the dialog palette data since we have switched palettes.
        self.palette_dialog.set_palette(palette_image)
        # Update the zoom dialog to the current sprite.
        self.zoom_dialog.set_sprite(zoom_image)
        # Do not show the palette or zoom dialogs until after we have set the palette/sprite information on them.
        # If we show them prior to this then the dialog graphics view does not correctly update
        # until we change the current palette.

        # Show our palette dialog if we need to.
        if self.palette_dialog.isHidden():
            self.palette_dialog.show()

        # Show our zoom dialog if we need to.
        if self.zoom_dialog.isHidden():
            self.zoom_dialog.show()

        self.reload_palette = False

    def _sprite_list_empty(self):
        """
        If we don't have any top level items then our sprite list is empty.
        """
        return self.ui.sprite_list.topLevelItem(0) is None

    def refresh(self):
        """
        Update the sprite list to the current palette.
        We also update the sprite preview but only if a sprite is selected.
        """
        character_id = self.ui.char_select.currentIndex()
        palette_num = self.ui.palette_select.currentData()

        if self._sprite_list_empty():
            self._populate_sprite_list(character_id)

        self._update_sprite_list(palette_num)

        sprite_item = self.ui.sprite_list.currentItem()
        if sprite_item is not None and not isinstance(sprite_item, SpriteGroupItem):
            self._refresh()

    def _iterate_sprite_groups(self):
        """
        Iterate the top level items in our sprite list.
        """
        top_level_index = 0
        while True:
            top_level_item = self.ui.sprite_list.topLevelItem(top_level_index)

            if top_level_item is None:
                break

            yield top_level_item
            top_level_index += 1

    @staticmethod
    def _iterate_sprite_files(top_level_item):
        """
        Iterate the child items of the given top level item.
        """
        sprite_index = 0

        while True:
            sprite_item = top_level_item.child(sprite_index)

            if sprite_item is None:
                break

            yield sprite_item
            sprite_index += 1

    def _update_sprite_list(self, palette_num):
        """
        Iterate our sprite list and set the palette number on our file items.
        This way the HPL file basename can be formatted to the correct palette.
        """
        for top_level_item in self._iterate_sprite_groups():
            for sprite_item in self._iterate_sprite_files(top_level_item):
                sprite_item.palette_num = palette_num

    @staticmethod
    def _add_hip_items(parent_item, hip_file_list, hpl_fmt):
        """
        Add all our HIP image files as a `SpriteFileItem` to the parent `SpriteGroupItem`.
        We associate an HPL palette file name format to each file item so we can dynamically
        select a palette on a per-image basis.
        """
        for hip_full_path in hip_file_list:
            hip_file = os.path.basename(hip_full_path)
            parent_item.addChild(SpriteFileItem(hip_full_path, hip_file, hpl_fmt))

    def _add_sprite_groups(self, cache_dir, palette_map):
        """
        We group together sprites by the palette files associated to them.
        """
        total_files = set()

        for name, data in palette_map.items():
            parent_item = SpriteGroupItem(name)
            self.ui.sprite_list.addTopLevelItem(parent_item)

            hpl_fmt = data[PALETTE_FILE]
            hip_file_list = [os.path.join(cache_dir, hip_file) for hip_file in data[HIP_FILE_LIST]]

            self._add_hip_items(parent_item, hip_file_list, hpl_fmt)
            total_files.update(hip_file_list)

        return total_files

    def _populate_sprite_list(self, character_id):
        """
        Populate the sprite list with our character sprite files.
        """
        character_name, character = CHARACTER_INFO[character_id]
        ext_info = CHARACTER_EXT_INFO[character_id]

        sprite_cache_path = self.paths.get_sprite_cache_path(character)
        effect_cache_path = self.paths.get_effect_cache_path(character)

        sprite_parent = SpriteGroupItem("Character")
        self.ui.sprite_list.addTopLevelItem(sprite_parent)

        sprite_files = set(self.paths.get_sprite_cache(character))
        sprite_files |= set(self.paths.get_effect_cache(character))

        with block_signals(self.ui.sprite_list):
            # Look for any sprite-specific palettes.
            sprite_palette_map = ext_info.get(SPRITE_PALETTE_MAP, {})
            added_files = self._add_sprite_groups(sprite_cache_path, sprite_palette_map)
            # If we found any we need to remove them from the files that will get grouped
            # under the "Character" parent item.
            sprite_files -= added_files

            # Look for any effect-specific palettes.
            effect_palette_map = ext_info.get(EFFECT_PALETTE_MAP, {})
            added_files = self._add_sprite_groups(effect_cache_path, effect_palette_map)
            # If we found any we need to remove them from the files that will get grouped
            # under the "Character" parent item.
            sprite_files -= added_files

            # We want our remaining sprites to be sorted.
            sprite_file_list = list(sprite_files)
            sprite_file_list.sort()

            # TODO: Eventually the extended info should be all we need? Still working that out.
            if ext_info:
                base_palette_fmt = ext_info[DEFAULT_PALETTE_FILE]
                self._add_hip_items(sprite_parent, sprite_file_list, base_palette_fmt)

            # TODO: Remove this. It exists to make characters without extended info work temporarily.
            else:
                self._add_hip_items(sprite_parent, sprite_file_list, f"{character}{{}}_00.hpl")

    def select_sprite(self):
        """
        A new sprite has been selected.
        Update our image preview with the new sprite.
        """
        sprite_item = self.ui.sprite_list.currentItem()

        if isinstance(sprite_item, SpriteGroupItem):
            return

        hip_full_path = sprite_item.hip_full_path
        hip_file = sprite_item.hip_file

        try:
            png_data = io.BytesIO()
            hip_to_png(hip_full_path, png_data)
            self.sprite.load_png(png_data)

        except Exception:
            self.show_error_dialog("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")
            return

        self._refresh()

    def mouse_move_event(self, evt):
        """
        Move the zoom dialog centerpoint to follow the mouse cursor.
        """
        motion_point = Qt.QPoint(evt.x(), evt.y())
        mapped_point = self.ui.sprite_preview.mapToScene(motion_point)
        self.zoom_dialog.move_cursor(mapped_point)
        self.crosshair.setPos(mapped_point)
        # Ensure the graphics view is refreshed so our crosshair colors update.
        self.ui.sprite_preview.viewport().update()

    def _set_color(self, palette_index, color_tuple):
        """
        The color in a palette has been changed by the user.
        Save the changes to disk and update the character visuals live.
        """
        palette_id = self.ui.palette_select.currentText()
        character_name = self.ui.char_select.currentText()
        character = self.ui.char_select.currentData()

        try:
            self.palette.set_index_color(palette_index, color_tuple)

        except Exception:
            message = f"Failed to change the color for palette index {palette_index}!"
            self.show_error_dialog("Error Updating Palette", message)
            return

        sprite_item = self.ui.sprite_list.currentItem()
        hpl_file_path = self.paths.get_edit_palette_path(character, palette_id)
        palette_full_path = os.path.join(hpl_file_path, sprite_item.hpl_file)

        try:
            self.palette.save_hpl(palette_full_path)

        except Exception:
            message = f"Failed to update palette {palette_id} for {character_name}!"
            self.show_error_dialog("Error Updating Palette", message)
            return

        self.refresh()
        self.image_data_changed.emit()

    def _choose_color(self, palette_index):
        """
        Choose a color for the given palette index.
        Show a QColorDialog to choose the color, with an initial color grabbed from the palette data
        that is associated to the given palette index.
        A bool indicating the dialog accept status and the selected color are returned.
        """
        try:
            current_color = self.palette.get_index_color(palette_index)

        except Exception:
            message = f"Failed to fetch the color for palette index {palette_index}!"
            self.show_error_dialog("Error Reading Palette", message)
            return False, ()

        initial = Qt.QColor(*current_color)
        dialog = QtWidgets.QColorDialog(initial, parent=self)
        dialog.setOptions(QtWidgets.QColorDialog.ShowAlphaChannel)

        accepted = dialog.exec_()

        qcolor = dialog.currentColor()
        color_tuple = (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())

        return accepted, color_tuple

    def choose_color_from_index(self, palette_index):
        """
        Pick a color for the given palette index.
        Either the palette dialog was double clicked and emitted `index_selected` or
        the sprite preview was double clicked and we have converted the mouse coordinates
        to a palette index.
        """
        accepted, color_tuple = self._choose_color(palette_index)
        if accepted:
            self._set_color(palette_index, color_tuple)

    def choose_color_from_coord(self, evt):
        """
        We have double clicked on the sprite preview.
        Get the (x, y) coordinate of the click within the graphics view and map it to
        an (x, y) coordinate within the scene (i.e. the sprite image).
        We can use the mapped coordinated to get the palette index of the color we clicked on.
        Finally we can use the palette index to choose a new color.
        """
        x = evt.x()
        y = evt.y()

        mapped_point = self.ui.sprite_preview.mapToScene(Qt.QPoint(x, y)).toPoint()

        try:
            palette_index = self.sprite.get_palette_index((mapped_point.x(), mapped_point.y()))

        except Exception:
            self.show_error_dialog("Error Getting Palette Index", f"Failed to get palette index of selected color!")
            return

        # Check if the palette index associated to the mouse event was swapped from a character
        # state change, and if so get the swap index as that is the index for which we should edit the color.
        sprite_item = self.ui.sprite_list.currentItem()
        if sprite_item is not None and not isinstance(sprite_item, SpriteGroupItem):
            swap_index = self.state.get_swap_of(sprite_item, palette_index)

            if swap_index is not None:
                palette_index = swap_index

        self.choose_color_from_index(palette_index)

    def _reset(self):
        """
        An internal only partial-reset.
        Resets everything except character selection so we can
        use this method in `select_character`.
        """
        self.state.hide()

        with block_signals(self.ui.palette_select):
            self.ui.palette_select.setCurrentIndex(-1)

        with block_signals(self.ui.slot_select):
            self.ui.slot_select.setEnabled(False)
            self.ui.slot_select.clear()
            self.ui.slot_select.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

        with block_signals(self.ui.sprite_list):
            self.ui.sprite_list.clear()

        self._clear_sprite_data()

    def reset(self):
        """
        Reset the editor state. We reset character, palette, and slot select, as well as
        the sprite file list and sprite image data.
        """
        with block_signals(self.ui.char_select):
            self.ui.char_select.setCurrentIndex(-1)

        self._reset()

    def set_selection_enable(self, state):
        """
        Set the enable state of the character group.
        Used to enable or disable the character, palette, and slot selection widgets.
        """
        self.ui.character_group.setEnabled(state)

    def close_dialogs(self):
        """
        Close both dialogs associated to the editor.
        """
        self.palette_dialog.hide()
        self.zoom_dialog.hide()
        self.state.hide()

    def show_error_dialog(self, *args, **kwargs):
        """
        Wrapper for `MainWindow.show_error_dialog()` solely to save line length.
        """
        self.mainwindow.show_error_dialog(*args, **kwargs)
