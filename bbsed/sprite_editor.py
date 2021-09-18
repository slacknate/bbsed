import io
import os
import json

from PyQt5 import Qt, QtCore, QtGui, QtWidgets

from libhip import HIPImage
from libhpl import PNGPalette, PNGPaletteImage
from libscr.commands import CMD_SPRITE

from .ui.sprite_editor_ui import Ui_Editor
from .ui.selector_widget_ui import Ui_Selector
from .ui.extra_widget_ui import Ui_Extra

from .animation_prep import AnimationPrepThread
from .animation_dialog import AnimationDialog
from .palette_dialog import COLOR_BOX_SIZE, PaletteDialog
from .zoom_dialog import ZoomDialog
from .crosshair import Crosshair
from .char_info import *
from .util import *

CROSS_HAIR_SIZE = 20

HIP_FILE_ROLE = QtCore.Qt.ItemDataRole.UserRole

COLUMN_ANIMATIONS = 0

SPRITE_PREFIX_LEN = 8
EFFECT_PREFIX_LEN = 8

SCR_FILE_FMT = "scr_{}.json"
SCR_EFFECT_FILE_FMT = "scr_{}ea.json"


def get_other(two_tuple, item):
    """
    Simple boolean logic trick. A two-tuple has two items and thus an item contained can only
    possibly have an index of 0 or 1. If we logically invert the index of the item we are given
    convert the result back to int we get the index of the other item in the tuple.
    """
    index = two_tuple.index(item)
    other_index = int(not index)
    return two_tuple[other_index]


class CharacterState:
    def __init__(self, sprite, sprite_editor):
        self.sprite = sprite
        self.sprite_editor = sprite_editor
        self.state_visible = sprite_editor.get_extra_visibility
        self.set_state_visibility = sprite_editor.set_extra_visibility
        self.get_state_name = None
        self.get_state = None
        self.palette_id = "INVALID"
        self.character_id = "INVALID"
        self.initial = None
        self.current = None

    def _show_states(self, state_name, state_choices):
        """
        Create and display a dialog for the given character that displays a character
        state (e.g. Izayoi Gain Art) and choices for the state.
        """
        def _make_state_callback():
            """
            Make a function that accepts the combobox string value and uses a closure of
            the state name to pass to a sprite editor method to handle state changes.
            """
            return lambda _state_value: self.sprite_editor.character_state_change(state_name, _state_value)

        self.sprite_editor.extra_controls.set_name(state_name)
        self.sprite_editor.extra_controls.set_choices(state_choices)
        self.sprite_editor.extra_controls.set_callback(_make_state_callback())

        self.get_state_name = lambda: state_name
        self.get_state = self.sprite_editor.extra_controls.get_state

        self.set_state_visibility(True)

    def set_palette_id(self, palette_id):
        """
        Update the character state to the current palette ID.
        """
        self.palette_id = palette_id

    def get_palette_id(self):
        """
        Fetch the current palette ID.
        """
        return self.palette_id

    def load_character(self, character_id):
        """
        Reset our character state information and determine if we have
        character state information that the user needs to be able to work with.
        """
        self.character_id = character_id
        self.current = None

        if self.state_visible():
            self.set_state_visibility(False)

        character_name, _ = CHARACTER_INFO[character_id]
        ext_info = CHARACTER_INFO_EXT.get(character_id, {})
        char_states = ext_info.get(CHARACTER_STATES, {})

        # If we have defined character states then we need parse the definition
        # into actionable data that this object can use.
        if char_states:
            self.current = self.initial = char_states[STATE_INITIAL]
            state_name, state_choices = char_states[STATE_DEFINITION]
            self._show_states(state_name, state_choices)

        else:
            self.set_state_visibility(False)

    def _update_state(self):
        """
        This method is used by the sprite editor in `SpriteEditor._refresh()`, and in
        that method we always reload the palette file.
        As such, we only need to swap colors if the current state choice is not the initial state as
        when the palette is reloaded the initial state is automatically displayed.
        Note that we also ensure that the given sprite item has a palette that requires a swap in the first place.
        """
        is_initial = True

        # Only attempt to fetch the character state if there is a state to be fetched!
        if self.state_visible():
            state = self.get_state()
            is_initial = (state == self.initial)
            self.current = state

        return is_initial

    def swap_colors(self):
        """
        Swap the colors of the relevant palette indices.

        Note that the way this works is that we only swap the colors when not
        in the initial character state.

        When a sprite is selected, the current selected palette is applied to the
        sprite. This means we need to swap the colors every time a sprite is loaded,
        as on sprite select the unswapped colors are always set on the image.
        """
        ext_info = CHARACTER_INFO_EXT.get(self.character_id, {})
        char_states = ext_info.get(CHARACTER_STATES, {})
        swap_colors = char_states.get(STATE_CHANGE, {}).get(SWAP_COLORS, ())

        is_initial = self._update_state()

        if not is_initial:
            for index1, index2 in swap_colors:
                color1, color2 = self.sprite.get_index_color_range(index1, index2)
                self.sprite.set_index_color_range((index1, color2), (index2, color1))

    def swap_palettes(self, sprite_item):
        """
        Swap the palette of this sprite item if it uses a palette associated to the character state.

        Note that the way this works is that we only swap the palettes when not
        in the initial character state.
        """
        ext_info = CHARACTER_INFO_EXT.get(self.character_id, {})
        char_states = ext_info.get(CHARACTER_STATES, {})
        swap_palettes = char_states.get(STATE_CHANGE, {}).get(SWAP_PALETTES, ())

        is_initial = self._update_state()

        for swap_files in swap_palettes:
            hpl_fmt = sprite_item.hpl_fmt

            # If our item HPL format is in the swap tuple then we need to get the format
            # that is NOT the one currently associated to the item and assign it.
            if hpl_fmt in swap_files:
                swap_palette = None

                # Each the swap data is a tuple of two HPL formats.
                if not is_initial:
                    swap_palette = get_other(swap_files, hpl_fmt)

                sprite_item.swap_hpl_fmt = swap_palette

    def get_swap_of(self, index):
        """
        When we fetch the palette index of a double clicked pixel we need to
        check if that palette index is an index that has been swapped.
        We return `None` if there is no defined swap index and ensure that
        we actually had to swap in the first place before getting our swap index.
        """
        swap_index = None
        is_initial = self._update_state()

        if not is_initial:
            ext_info = CHARACTER_INFO_EXT.get(self.character_id, {})
            char_states = ext_info.get(CHARACTER_STATES, {})
            swap_colors = char_states[STATE_CHANGE].get(SWAP_COLORS, ())

            for swap in swap_colors:
                if index in swap:
                    swap_index = get_other(swap, index)
                    break

        return swap_index


class SpriteGroupItem(QtWidgets.QTreeWidgetItem):
    """
    Top level item in the sprite list to represent a group of HIP images that share an HPL palette file.
    """
    def __init__(self, name):
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.name = name

    def data(self, column, role):
        if column == COLUMN_ANIMATIONS and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.name


class SpriteFileItem(QtWidgets.QTreeWidgetItem):
    """
    Child item in the sprite list to represent a HIP image associated to the current selected character.
    """
    def __init__(self, hip_full_path, sprite_duration, hip_file, hpl_fmt):
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.hip_full_path = hip_full_path
        self.sprite_duration = sprite_duration
        self.hip_file = hip_file
        self.swap_hpl_fmt = None
        self.hpl_fmt = hpl_fmt
        self.palette_num = ""

    @property
    def name(self):
        """
        TODO: remove this when we no longer rely on it.
        """
        return self.hip_file

    @property
    def hpl_file(self):
        """
        Our HPL palette file is associated to a character and palette.
        The character abbreviation is already include in this string but
        the palette can change dynamically from the user interface.
        The palette number is updated when we call `SpriteEditor.refresh()`.
        Additionally, the palette file may also be swapped depending on character
        state controls for the selected character.
        """
        if self.swap_hpl_fmt is not None:
            _hpl_file = self.swap_hpl_fmt.format(self.palette_num)

        else:
            _hpl_file = self.hpl_fmt.format(self.palette_num)

        return _hpl_file

    def data(self, column, role):
        if column == COLUMN_ANIMATIONS and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.hip_file


class Sprite:
    def __init__(self):
        # If our loaded sprite is a raw RGBA image then this is object is used to manipulate said sprite.
        self.hip_image = HIPImage()
        # If our loaded sprite is a palette image then this is object is used to manipulate said sprite.
        self.palette_image = PNGPaletteImage()
        # The backend manager and visualization of our sprite palette.
        self.palette = PNGPalette(COLOR_BOX_SIZE)

    def is_palette_image(self):
        """
        Expose helper from the HIP image to determine if this sprite is a palette image.
        """
        return self.hip_image.is_palette_image()

    def load_sprite(self, hip_full_path):
        """
        Load our sprite from the source HIP image.
        If the image is a palette image we update the palette image with a PNG conversion of the HIP image.
        """
        self.hip_image.load_hip(hip_full_path)

        if self.hip_image.is_palette_image():
            png_image = io.BytesIO()
            self.hip_image.save_png(png_image)

            png_image.seek(0)
            self.palette_image.load_png(png_image)

    # TODO: save_sprite

    def get_index_color_range(self, *indices):
        """
        Expose color range fetch method from the sprite palette image.
        This is used exclusively by the `CharacterState.swap_colors` method.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        return self.palette_image.get_index_color_range(*indices)

    def set_index_color_range(self, *index_colors):
        """
        Expose color range set method from the sprite palette image.
        This is used exclusively by the `CharacterState.swap_colors` method.
        When we color swap, we do not want to swap the actual palette colors, just the displayed
        colors in the preview. Thus we only manipulate the palette image and not the palette itself.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        self.palette_image.set_index_color_range(*index_colors)

    def get_palette_index(self, pixel):
        """
        Expose method to fetch palette index via pixel coordinate from the sprite palette image.
        Used by the sprite editor to set color from a double-clicked (x, y) coordinate of the sprite.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        return self.palette_image.get_palette_index(pixel)

    def get_index_color(self, index):
        """
        Expose method to fetch palette color via palette index.
        Used by the sprite editor to get the initial color for the color dialog when
        selecting a new color.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        return self.palette.get_index_color(index)

    def set_index_color(self, index, rgba):
        """
        Expose method to set palette color via palette index.
        Used by the sprite editor to set the palette color from the color chosen by the user
        via the color dialog.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        self.palette.set_index_color(index, rgba)

    def load_palette(self, hpl_full_path):
        """
        The sprite preview is being reloaded and we should re-load the palette associated to this sprite.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        self.palette.load_hpl(hpl_full_path)
        self.palette_image.load_hpl(hpl_full_path)

    def save_palette(self, hpl_full_path):
        """
        Save our palette changes to disk.
        The user has selected a new color and we should preserve this change.
        """
        if not self.hip_image.is_palette_image():
            raise TypeError("Loaded image is not a palette image!")

        self.palette.save_hpl(hpl_full_path)

    def get_preview_image(self):
        """
        Get the image for display in the sprite preview.
        Note that our preview comes from a different source depending on if
        it is a palette image or not.
        """
        png_preview = io.BytesIO()

        if self.hip_image.is_palette_image():
            self.palette_image.save_png(png_preview)

        else:
            self.hip_image.save_png(png_preview)

        return png_preview.getvalue()

    def get_palette_visualization(self):
        """
        Get the visualization of the palette for this sprite.
        If the loaded sprite is not a palette image then we return no data.
        """
        palette_image = io.BytesIO()

        if self.hip_image.is_palette_image():
            self.palette.save_png(palette_image)

        return palette_image.getvalue()


class EditorSelector(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.ui = Ui_Selector()
        self.ui.setupUi(self)

    @property
    def character(self):
        """
        Convenience property to abbreviate usages of this combobox in the sprite editor.
        """
        return self.ui.char_select

    @property
    def palette(self):
        """
        Convenience property to abbreviate usages of this combobox in the sprite editor.
        """
        return self.ui.palette_select

    @property
    def slot(self):
        """
        Convenience property to abbreviate usages of this combobox in the sprite editor.
        """
        return self.ui.slot_select


class ExtraControls(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.ui = Ui_Extra()
        self.ui.setupUi(self)

        self.callback = None

    def set_name(self, name):
        """
        Set the name of this character state selector.
        """
        self.ui.state_name.setText(name)

    def set_choices(self, choices):
        """
        Set the valid choices for the character state selector.
        We clear any previously added choices first.
        """
        self.ui.state_choices.clear()
        self.ui.state_choices.addItems(choices)

    def get_state(self):
        """
        Get the current selected character state.
        """
        return self.ui.state_choices.currentText()

    def set_callback(self, callback):
        """
        Set the callback for character state change.
        If a callback has been set previously we remove it before adding the new callback.
        """
        if self.callback is not None:
            self.ui.state_choices.currentTextChanged.disconnect(self.callback)

        self.ui.state_choices.currentTextChanged.connect(callback)
        self.callback = callback


class SpriteEditor(QtWidgets.QWidget):

    image_data_changed = QtCore.pyqtSignal()
    character_changed = QtCore.pyqtSignal(str, str)
    palette_changed = QtCore.pyqtSignal(str, str)
    palette_slot_changed = QtCore.pyqtSignal(str, int)

    def __init__(self, mainwindow, paths, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.ui = Ui_Editor()
        self.ui.setupUi(self)

        # The sprite we are currently editing.
        self.sprite = Sprite()
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

        # Create our extra controls widget and add it to the toolbar.
        # Hide the extra controls by default as there are no controls to display when no character is selected.
        self.extra_controls = ExtraControls(self)
        self.extra_separator = self.mainwindow.ui.toolbar.addSeparator()
        self.ex_ctrl_action = self.mainwindow.ui.toolbar.addWidget(self.extra_controls)
        self.set_extra_visibility(False)

        # Create our character/palette/slot selector widget and add it to the toolbar.
        self.selector = EditorSelector(self)
        self.mainwindow.ui.toolbar.insertWidget(self.mainwindow.ui.cut_color, self.selector)
        self.mainwindow.ui.toolbar.insertSeparator(self.mainwindow.ui.cut_color)

        for _, (character_name, character) in sorted_chars:
            self.selector.character.addItem(character_name, character)

        # Set up character, palette, and save slot UI callbacks.
        # By default no character is selected.
        self.selector.character.setCurrentIndex(-1)
        self.selector.character.currentIndexChanged.connect(self.select_character)
        self.selector.palette.currentIndexChanged.connect(self.select_palette)
        self.selector.slot.currentIndexChanged.connect(self.select_palette_slot)

        # Create editor related dialogs and associate them to their respective View Menu check items.
        self.zoom_dialog = ZoomDialog(self.mainwindow.ui.view_zoom, parent=mainwindow)
        self.palette_dialog = PaletteDialog(self.mainwindow.ui.view_palette, parent=mainwindow)
        self.palette_dialog.index_selected.connect(self.choose_color_from_index)

        # FIXME: Drag select off-by-one issue still present.
        # Set the selection mode and selection callbacks for the sprite file list.
        self.ui.sprite_list.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)
        self.ui.sprite_list.itemSelectionChanged.connect(self.select_sprite)
        # Set up the sprite file list context menu.
        self.ui.sprite_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.sprite_list.customContextMenuRequested.connect(self._show_image_menu)
        # Set up the callback for playing animations.
        self.ui.play_animation.triggered.connect(self.show_animation_dialog)

        # Ensure that we center the view on our sprite scene.
        self.ui.sprite_preview.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.ui.sprite_preview.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)

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
        character_name = self.selector.character.currentText()
        character = self.selector.character.currentData()
        return character_name, character

    def find_character(self, character_name=None, character=None):
        """
        Find a character. We allow for finding a character via name or by abbreviation.
        """
        character_id = -1

        if character_name is None and character is None:
            raise ValueError("Must provide either a character name or a character abbreviation!")

        if character_name:
            character_id = self.selector.character.findText(character_name)

        if character:
            character_id = self.selector.character.findData(character)

        return CHARACTER_INFO[character_id]

    def get_palette(self):
        """
        Get the palette ID and palette number of the current selected palette.
        A palette ID is the number displayed in game, a palette number is the number used in the files on disk.
        """
        palette_id = self.selector.palette.currentText()
        palette_num = self.selector.palette.currentData()
        return palette_id, palette_num

    def get_slot(self):
        """
        Get the palette slot name and slot typeof the current selected palette slot.
        """
        slot_name = self.selector.slot.currentText()
        slot_type = self.selector.slot.currentData()
        return slot_name, slot_type

    def set_slot(self, slot_name=None, slot_type=None):
        """
        Set the current palette slot. We allow for setting by name or type.
        """
        slot_index = -1

        if slot_name is None and slot_type is None:
            raise ValueError("Must provide either a slot name or a slot type!")

        if slot_name:
            slot_index = self.selector.slot.findText(slot_name)

        if slot_type:
            slot_index = self.selector.slot.findData(slot_type)

        self.selector.slot.setCurrentIndex(slot_index)

    def delete_slot(self, save_name):
        """
        We have deleted the save slot identified by `save_name`. We should remove it from the UI.
        """
        save_index = self.selector.slot.findText(save_name)

        with block_signals(self.selector.slot):
            self.selector.slot.removeItem(save_index)

        # Re-select the edit slot after we delete a palette.
        self.selector.slot.setCurrentIndex(0)

    def import_palette_data(self, character, palette_id, hpl_to_import, pac_to_import):
        """
        We have successfully imported palette data. Update the UI to include the new palettes if applicable.
        """
        with block_signals(self.selector.slot):
            for save_char, save_pal_id, save_name in hpl_to_import.keys():
                if save_char == character and save_pal_id == palette_id:
                    self.selector.slot.addItem(save_name, PALETTE_SAVE)

            for file_info in pac_to_import.values():
                for save_char, save_pal_id, save_name in file_info.keys():
                    if save_char == character and save_pal_id == palette_id:
                        self.selector.slot.addItem(save_name, PALETTE_SAVE)

    def add_save_slot(self, slot_name):
        """
        We have saved a palette. Add the slot name to the UI if necessary and select the slot.
        """
        # We may be saving changes made to a palette that already has a save name.
        save_index = self.selector.slot.findText(slot_name)

        with block_signals(self.selector.slot):
            # Only add a new item if this save name is new.
            # This will happen if the palette has not been saved before
            # or if the user has selected the "Save As" option.
            if save_index < 0:
                self.selector.slot.addItem(slot_name, PALETTE_SAVE)
                save_index = self.selector.slot.findText(slot_name)

            self.selector.slot.setCurrentIndex(save_index)

        # If this is the first palette saved for this character and palette ID then we will need to enable
        # the save select combobox.
        if not self.selector.slot.isEnabled():
            self.selector.slot.setEnabled(True)

    def _update_save_slots(self, character_saves):
        """
        We have selected a character or a palette.
        We need to update the available slots presented in the UI.
        """
        with block_signals(self.selector.slot):
            # Clearing the save select and re-adding items will auto-select the first item
            # which will always be a non-saved palette.
            self.selector.slot.clear()
            self.selector.slot.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

            # Set the save select enable state based on the presence of files on disk.
            self.selector.slot.setEnabled(bool(character_saves))
            for save_name in character_saves:
                self.selector.slot.addItem(save_name, PALETTE_SAVE)

    def character_state_change(self, _, __):
        """
        Callback for stateful characters so the editor can respond to state changes
        controlled by a character "Extra Controls" dialog.
        Here we look for any palettes that we need to swap on sprite items.
        An example of sprite item palette swaps would be Izayoi's special moves; the
        slash effects change color depending on Gain Art.
        """
        self.refresh()

    def select_character(self):
        """
        A new character was picked from the character combobox.
        Note that we explicity DO NOT update the sprite list here.
        We need to wait for the mainwindow to perform sprite extraction (if necessary)
        and after that completes the mainwindow will invoke `SpriteEditor.refresh()`.
        """
        self._reset()

        character_id = self.selector.character.currentIndex()
        character_name = self.selector.character.currentText()
        character = self.selector.character.currentData()

        # Don't allow the user to interact with these parts of the UI while we are updating them.
        self.set_selection_enable(False)

        # Block signals while we add items so the signals are not emitted.
        # We do not want to try to select a palette before a sprite is selected, and
        # at the very least we do not want to spam the signals in a loop regardless.
        with block_signals(self.selector.palette):
            for palette_id, palette_num in iter_palettes():
                self.selector.palette.addItem(palette_id, palette_num)

            # Automatically select the first palette.
            # We intentionally select this in the block_signals block so we do not try to set
            # palette data before a sprite is selected.
            self.selector.palette.setCurrentIndex(0)

        # Get the palette ID from the widget for the sake of consistency.
        palette_id = self.selector.palette.currentText()

        # Update the UI to show any save slots for the first palette.
        character_saves = self.paths.get_character_saves(character, palette_id)
        self._update_save_slots(character_saves)

        # Load up the newly selected character information into our state manager.
        self.state.load_character(character_id)

        # Re-enable user interaction for everything else.
        self.set_selection_enable(True)

        self.character_changed.emit(character_name, character)

    def _lock_palette(self, character, character_name, palette_id):
        """
        Lock the given palette for editing. This prevents BBCF Sprite Editor
        instances from stepping on each others toes and otherwise corrupting or change palette data
        in undesirable ways.
        """
        prev_palette_id = self.state.get_palette_id()
        old_lock_file = self.paths.get_edit_lock_path(character, prev_palette_id)

        edit_palette = True
        lock_file = self.paths.get_edit_lock_path(character, palette_id)

        if owns_lock(old_lock_file):
            delete_lock(old_lock_file)

        if check_lock(lock_file):
            message = (f"{character_name} palette {palette_id} is locked by another BBCF Sprite Editor process. "
                       f"Do you want to edit the palette anyway? It is recommended "
                       f"to do this only if you know what you are doing.")
            edit_palette = self.show_confirm_dialog("Paletted Locked", message)

            if not edit_palette:
                # If the user has chosen not to edit the palette we select the previous palette.
                # This may in fact de-select a palette all together.
                with block_signals(self.selector.palette):
                    palette_index = self.selector.palette.findText(prev_palette_id)
                    self.selector.palette.setCurrentIndex(palette_index)

                # We also need to update our slot selection. If we are selected a valid previous
                # palette then we select the edit slow. Otherwise we also de-select all slots.
                with block_signals(self.selector.slot):
                    slot_index = 0 if palette_index >= 0 else -1
                    self.selector.slot.setCurrentIndex(slot_index)

        # We are for sure selecting this palette. Create the lock and update our state!
        if edit_palette:
            create_lock(lock_file)
            self.state.set_palette_id(palette_id)

        return edit_palette

    def select_palette(self):
        """
        A new palette has been selected.
        Replace the palette of the currently selected sprite and update the image preview.
        """
        character = self.selector.character.currentData()
        character_name = self.selector.character.currentText()
        palette_id = self.selector.palette.currentText()
        palette_num = self.selector.palette.currentData()

        # We have selected a new palette and should now lock it for editing.
        # If it is locked by another process and the user wishes to respect that we should not continue.
        if not self._lock_palette(character, character_name, palette_id):
            return

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
        slot_name = self.selector.slot.currentText()
        slot_type = self.selector.slot.currentData()

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
        # Reset our crosshair.
        self.crosshair = Crosshair(CROSS_HAIR_SIZE, False, 0, 0)
        # Clear palette data.
        self.palette_dialog.reset()
        # Clear zoom view.
        self.zoom_dialog.reset()

    def _refresh_palette(self):
        """
        Refresh our sprite palette. Reload the palette file, apply it to the sprite, and
        look for any color swaps that are applicable.
        """
        character = self.selector.character.currentData()
        slot_name = self.selector.slot.currentText()
        slot_type = self.selector.slot.currentData()
        palette_id = self.selector.palette.currentText()
        sprite_item = self.ui.sprite_list.currentItem()

        # We only need to palette swap if we have an active item.
        if sprite_item is not None and not isinstance(sprite_item, SpriteGroupItem):
            self.state.swap_palettes(sprite_item)

        # If we have a saved palette selected we should display that palette.
        if slot_type == PALETTE_SAVE:
            save_name = slot_name
            hpl_file_path = self.paths.get_character_save_path(character, palette_id, save_name)

        # Otherwise display the edit slot data.
        else:
            hpl_file_path = self.paths.get_edit_palette_path(character, palette_id)

        hpl_full_path = os.path.join(hpl_file_path, sprite_item.hpl_file)

        try:
            self.sprite.load_palette(hpl_full_path)

        except Exception:
            self.show_error_dialog("Error Setting Palette", "Failed to update the selected palette!")
            return

        # We only need to color swap if we have an active item.
        if sprite_item is not None and not isinstance(sprite_item, SpriteGroupItem):
            self.state.swap_colors()

    def _refresh(self):
        """
        Update the sprite preview with the given palette index.
        If no index is provided we assume that the current index is to be used.
        This method is only invoked when we pick a new sprite or select a new palette.
        Our cached sprite uses a palette from the sprite data definition, NOT from the
        in-game palette data. This means that we should always be re-writing the palette.
        """
        is_palette = self.sprite.is_palette_image()

        # If we have a palette we need to refresh it.
        if is_palette:
            self._refresh_palette()

        # Hide our palette dialog if we need to.
        # RGBA images do not feature a palette.
        else:
            self.mainwindow.ui.view_palette.setEnabled(False)
            if self.palette_dialog.isVisible():
                self.palette_dialog.hide()

        # Get the raw PNG data of our palette visualization so we can pass it to the palette dialog.
        palette_image = self.sprite.get_palette_visualization()
        # Get the raw PNG of our sprite so we can load it into the sprite preview as a pixmap.
        sprite_image = self.sprite.get_preview_image()
        # Make a copy for the zoom dialog so it can "read" the image and scale it.
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

        # Update the dialog palette data since we may have switched palettes.
        self.palette_dialog.set_palette(palette_image)
        # Update the zoom dialog to the current sprite.
        self.zoom_dialog.set_sprite(zoom_image)
        # Do not show the palette or zoom dialogs until after we have set the palette/sprite information on them.
        # If we show them prior to this then the dialog graphics view does not correctly update
        # until we change the current palette.

        # Show our palette dialog if we need to.
        if is_palette:
            self.mainwindow.ui.view_palette.setEnabled(True)

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
        character_id = self.selector.character.currentIndex()
        character_name = self.selector.character.currentText()
        character = self.selector.character.currentData()
        palette_id = self.selector.palette.currentText()
        palette_num = self.selector.palette.currentData()

        # Do not try to populate the sprite list if no character is selected or if
        # it has already has been populated. The sprite list is cleared on reset so
        # we will only populate this list once per character selection.
        if character_id in CHARACTER_INFO and self._sprite_list_empty():
            self._populate_sprite_list(character_id)

            # If we have to populate the sprite list then we have just selected a character.
            # At this point we should attempt to lock the palette that character select has given us.
            # If it is locked by another process and the user wishes to respect that we should not continue.
            if not self._lock_palette(character, character_name, palette_id):
                return

        self._update_sprite_list(palette_num)

        sprite_item = self.ui.sprite_list.currentItem()
        if sprite_item is not None and not isinstance(sprite_item, SpriteGroupItem):
            self._refresh()

    def _iterate_sprite_files(self, parent_item=None, recurse=True):
        """
        Iterate the files in our sprite list.
        """
        item_index = 0

        while True:
            if parent_item is not None:
                item = parent_item.child(item_index)
            else:
                item = self.ui.sprite_list.topLevelItem(item_index)

            if item is None:
                break

            if isinstance(item, SpriteGroupItem) and recurse:
                yield from self._iterate_sprite_files(item)
            else:
                yield item

            item_index += 1

    def _update_sprite_list(self, palette_num):
        """
        Iterate our sprite list and set the palette number on our file items.
        This way the HPL file basename can be formatted to the correct palette.
        """
        for sprite_item in self._iterate_sprite_files():
            sprite_item.palette_num = palette_num

    @staticmethod
    def _add_hip_items(parent_item, hip_file_list, hpl_fmt):
        """
        Add all our HIP image files as a `SpriteFileItem` to the parent `SpriteGroupItem`.
        We associate an HPL palette file name format to each file item so we can dynamically
        select a palette on a per-image basis.
        """
        for hip_full_path, sprite_duration in hip_file_list:
            hip_file = os.path.basename(hip_full_path)
            parent_item.addChild(SpriteFileItem(hip_full_path, sprite_duration, hip_file, hpl_fmt))

    def _get_or_create_group(self, name, parent_item=None):
        """
        Get a group item by name. If a parent item is provided we look for
        children of that item to match. If we cannot find an item with the
        given name we create one.
        """
        item_index = 0

        while True:
            if parent_item is not None:
                item = parent_item.child(item_index)
            else:
                item = self.ui.sprite_list.topLevelItem(item_index)

            if item is None:
                item = SpriteGroupItem(name)

                if parent_item is not None:
                    parent_item.addChild(item)
                else:
                    self.ui.sprite_list.addTopLevelItem(item)

            if item.name == name:
                return item

            item_index += 1

    def _populate_script_sprites(self, nodes, sprite_cache_path, default_palette_fmt):
        """
        Read a parsed bbscript file and find all character sprites.
        """
        for node in nodes:
            sprite_file_data = []

            for nested_node in node["body"]:
                if nested_node["cmd_id"] == CMD_SPRITE:
                    sprite_file_data.append(nested_node["cmd_args"])

            if sprite_file_data:
                animation_name = node["cmd_args"][0]
                hip_file_list = []

                for sprite_name, sprite_duration in sprite_file_data:
                    hip_full_path = os.path.join(sprite_cache_path, sprite_name + ".hip")
                    hip_file_list.append((hip_full_path, sprite_duration))

                parent_item = self._get_or_create_group(animation_name)
                self._add_hip_items(parent_item, hip_file_list, default_palette_fmt)

    def _populate_sprite_list(self, character_id):
        """
        Populate the sprite list with our character sprite files.
        """
        character_name, character = CHARACTER_INFO[character_id]

        # Lambda uses the same character abbreviation in the sprite files (but not script files?) because reasons.
        file_character = character
        if character == "rm":
            file_character = "ny"

        default_palette_fmt = DEFAULT_PALETTE_FMT.format(file_character)

        sprite_cache_path = self.paths.get_sprite_cache_path(character)
        script_cache_path = self.paths.get_script_cache_path(character)

        for scr_fmt in (SCR_FILE_FMT, SCR_EFFECT_FILE_FMT):
            script_path = os.path.join(script_cache_path, scr_fmt.format(character))

            with open(script_path, "r") as ast_fp:
                nodes = json.load(ast_fp)

            self._populate_script_sprites(nodes, sprite_cache_path, default_palette_fmt)

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
            self.sprite.load_sprite(hip_full_path)

        except Exception:
            self.show_error_dialog("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")
            return

        self._refresh()

    def _show_image_menu(self, _):
        """
        Popup the HIP file list context menu at the cursor.
        """
        selected_sprite = self.ui.sprite_list.currentItem()

        image_menu = QtWidgets.QMenu(parent=self)
        image_menu.addAction(self.ui.play_animation)
        if selected_sprite.parent() is not None:
            image_menu.addAction(self.ui.detail_img_info)

        image_menu.popup(QtGui.QCursor().pos())

    def _get_animation_files(self, selected_item, character):
        """
        Return the current palette file name as well as the image files assocaited to the selected animation.
        """
        parent_item = selected_item.parent()

        # We have selected a top-level group item which thus serves as our parent item.
        if parent_item is None:
            parent_item = selected_item

        frame1 = parent_item.child(0)
        palette_id = self.selector.palette.currentText()
        hpl_file_path = self.paths.get_edit_palette_path(character, palette_id)
        palette_full_path = os.path.join(hpl_file_path, frame1.hpl_file)

        frame_files = []
        for frame_item in self._iterate_sprite_files(parent_item, recurse=False):
            frame_files.append((frame_item.hip_full_path, frame_item.sprite_duration))

        return palette_full_path, frame_files

    def show_animation_dialog(self, _):
        """
        Show the animation dialog so we can play an animation as we would see it in game.
        """
        selected_item = self.ui.sprite_list.currentItem()
        character = self.selector.character.currentData()

        palette_full_path, frame_files = self._get_animation_files(selected_item, character)

        # Extract prepare data needed to render the animation.
        thread = AnimationPrepThread(character, self.paths, palette_full_path, frame_files)
        if not self.mainwindow.run_work_thread(thread, "Animation Prep", "Loading animation data into memory..."):
            # If our preparation procedure did not succeed we return early to avoid problems displaying the animation.
            return

        dialog = AnimationDialog(thread.frames, thread.chunks, thread.hitboxes, thread.hurtboxes, parent=self)
        dialog.show()

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
        palette_id = self.selector.palette.currentText()
        character_name = self.selector.character.currentText()
        character = self.selector.character.currentData()

        try:
            self.sprite.set_index_color(palette_index, color_tuple)

        except Exception:
            message = f"Failed to change the color for palette index {palette_index}!"
            self.show_error_dialog("Error Updating Palette", message)
            return

        sprite_item = self.ui.sprite_list.currentItem()
        hpl_file_path = self.paths.get_edit_palette_path(character, palette_id)
        palette_full_path = os.path.join(hpl_file_path, sprite_item.hpl_file)

        try:
            self.sprite.save_palette(palette_full_path)

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
            current_color = self.sprite.get_index_color(palette_index)

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
        # If the current image is not a palette image then we cannot pick a color as there is no palette.
        if not self.sprite.is_palette_image():
            return

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
            swap_index = self.state.get_swap_of(palette_index)

            if swap_index is not None:
                palette_index = swap_index

        self.choose_color_from_index(palette_index)

    def _reset(self):
        """
        An internal only partial-reset.
        Resets everything except character selection so we can
        use this method in `select_character`.
        """
        with block_signals(self.selector.palette):
            self.selector.palette.setCurrentIndex(-1)

        with block_signals(self.selector.slot):
            self.selector.slot.setEnabled(False)
            self.selector.slot.clear()
            self.selector.slot.addItem(SLOT_NAME_EDIT, PALETTE_EDIT)

        with block_signals(self.ui.sprite_list):
            self.ui.sprite_list.clear()

        self._clear_sprite_data()

    def reset(self):
        """
        Reset the editor state. We reset character, palette, and slot select, as well as
        the sprite file list and sprite image data.
        """
        with block_signals(self.selector.character):
            self.selector.character.setCurrentIndex(-1)

        self._reset()

    def set_selection_enable(self, state):
        """
        Set the enable state of the character group.
        Used to enable or disable the character, palette, and slot selection widgets.
        """
        self.selector.character.setEnabled(state)
        self.selector.palette.setEnabled(state)
        self.selector.slot.setEnabled(state)

    def get_extra_visibility(self):
        """
        Get the visibility state of the extra controls.
        """
        return self.ex_ctrl_action.isVisible()

    def set_extra_visibility(self, state):
        """
        Set the visibility state of the extra controls.
        This includes the separator next to the extra controls widget.
        """
        self.ex_ctrl_action.setVisible(state)
        self.extra_separator.setVisible(state)

    def close(self):
        """
        Close all dialogs associated to the editor.
        We also clean up any palette lock files owned by this process.
        """
        self.palette_dialog.hide()
        self.zoom_dialog.hide()

        character = self.selector.character.currentData()
        palette_id = self.selector.palette.currentText()

        # If we have an active lock file remove it.
        if character is not None and palette_id is not None:
            lock_file = self.paths.get_edit_lock_path(character, palette_id)

            if owns_lock(lock_file):
                os.remove(lock_file)

    def show_confirm_dialog(self, *args, **kwargs):
        """
        Wrapper for `MainWindow.show_confirm_dialog()` solely to save line length.
        """
        return self.mainwindow.show_confirm_dialog(*args, **kwargs)

    def show_message_dialog(self, *args, **kwargs):
        """
        Wrapper for `MainWindow.show_message_dialog()` solely to save line length.
        """
        return self.mainwindow.show_message_dialog(*args, **kwargs)

    def show_error_dialog(self, *args, **kwargs):
        """
        Wrapper for `MainWindow.show_error_dialog()` solely to save line length.
        """
        self.mainwindow.show_error_dialog(*args, **kwargs)
