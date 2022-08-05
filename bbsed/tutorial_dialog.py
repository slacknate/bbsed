import os

from PyQt5 import QtCore, QtGui, QtWidgets

from .ui.tutorial_dialog_ui import Ui_Dialog

PAGE_0 = """
<html>
<body>
This tutorial aims to get you started on the path to editing or creating<br>
color palettes for any character of your choice! If you see any <a href="no_action">blue</a> text<br>
in the following pages, be sure to click it!
</body>
</html>
"""

PAGE_1 = """
<html>
<body>
To begin, first we need to set the Steam and BBCF installation directories.<br>
We can do this by going to the settings dialog from the <a href="file_menu">File</a> menu.
</body>
</html>
"""

PAGE_2 = """
<html>
<body>
Now we can select a character for which we want to make a custom palette.<br><br>

There are three dropdowns found on the left side of the toolbar.<br>
Selecting a character is done with the first <a href="char_select">dropdown</a>.<br><br>

Go ahead, select a character!
</body>
</html>
"""

PAGE_3 = """
<html>
<body>
The sprites for each character are grouped animations which are typically, but not<br>
always, associated to player input. Expand the first animation group. This will show<br>
all sprite files for that character animation.
</body>
</html>
"""

PAGE_4 = """
<html>
<body>
Select the first sprite file in the previously expanded animation group.<br>
A character sprite preview, as well as some new dialogs, have appeared!<br>
These dialogs provide useful information for editing a character palette.<br><br>

The Sprite Zoom dialog shows a 2X zoom of the currently displayed<br>
sprite image centered on the cursor. The Palette Data dialog displays<br>
the full palette for the displayed sprite image. This information is<br>
visualized as a 16x16 square of the 256 colors present in the palette.<br>
Note that not every color must be used in a sprite.<br><br>

The first color in any palette, displayed in the Palette Data dialog<br>
at the bottom right corner, is the "transparent" color for this sprite.<br>
This color will not be displayed in game.
</body>
</html>
"""

PAGE_5 = """
<html>
<body>
The editor allows for separately editing each color palette, by number, that the game allows<br>
players to choose in game. This can be done via the second <a href="pal_select">dropdown</a> found<br>
on the left side of the toolbar. Cycle through the list and see how the displayed<br>
palette changes.<br><br>

In this editor, each character palette also features something called "slots".<br>
A slot is what we call the save name for a custom palette. Every character features a slot<br>
for each entry in the BlazBlue series in which that character appears.
</body>
</html>
"""

PAGE_6 = """
<html>
<body>
To edit a palette color, you can double-click on the displayed sprite or on a<br>
color square in the Palette Data dialog.<br><br>

This will pop up a color selection dialog where you pick a color to replace the<br>
color you double-clicked on. Give it a shot!<br><br>

The window title will show an asterisk (*) if the current selected palette has active<br>
edits that have not been saved. Note that even though these changes are "unsaved" they<br>
are persistent if the app is closed.
</body>
</html>
"""

PAGE_7 = """
<html>
<body>
There are also several palette editing tools found in the <a href="edit_menu">Edit</a> menu and toolbar.<br><br>

These tools are enabled when a palette index selection has been made in the Palette Dialog.<br>
To make a selection, left click or left-click drag within the Palette Dialog.<br>
To remove a selection, right click the Palette Dialog.<br><br>

The Cut, Copy, Paste, and Fill tools function as would be expected.<br>
The Swap tool requires a second selection be made after activating the tool to pick the color to swap.<br>
The Gradient tool will create a color gradient that shifts between the first and last colors selected.<br>
Note that the "direction" of the gradient is determined by the order of the selection.<br>
The initial palette index selected is the start, the end is the palette index last click-dragged upon.<br><br>

Try making selection(s) and using the tools to edit some palette colors!
</body>
</html>
"""

PAGE_8 = """
<html>
<body>
To save active changes to a save slot, use the "Save" or "Save As" options found on the<br>
toolbar or in the <a href="pal_menu">Palettes</a> menu. A save slot can be created whether a palette has active<br>
edits or is completely unchanged. Let's create a slot and save your active changes!
</body>
</html>
"""

PAGE_9 = """
<html>
<body>
Your changes have been saved as the name you chose for this palette slot when prompted.<br>
This name will now appear in the third <a href="slot_select">dropdown</a> and<br>
you can recall this palette to view or edit whenever you like!<br><br>

Note that slots are bound to the specific palette number selected during editing,<br>
so be sure to check all palette numbers if you cannot find a specific save slot.<br><br>

A save slot can be deleted via the "Delete" option found on the toolbar or in the 
<a href="pal_menu">Palettes</a> menu.<br>
A save slot must be actively selected for the "Delete" option to be enabled.
</body>
</html>
"""

PAGE_10 = """
<html>
<body>
The fourth <a href="hpl_select">dropdown</a> is used to select which color set is currently being<br>
viewed and edited. Each character has 8 color sets that serve different purposes.<br>
Note that not all of these color sets may be used.<br><br>

Characters will commonly have different color sets for things such as effects,<br>
unique intro sprites, unique Astral sprites, etc. Experiment with the color sets<br>
to see what colors in the game you can edit!
</body>
</html>
"""

PAGE_11 = """
<html>
<body>
Note that there are also "Copy Palette", "Paste Palette", and "Discard Changes" options<br>
found in the <a href="pal_menu">Palettes</a> menu and toolbar.<br><br>

When "Copy" is activated the tool will copy the current selected palette<br>
slot. This occurs whether or not there are active changes. Palettes can be copied<br>
regardless of presence of unsaved changes.<br><br>

When "Paste" is activated the tool will overwrite the current selected<br>
palette slot with a previously been copied palette.<br>
This will clear the palette clipboard.<br><br>

The "Discard" option will remove any unsaved changes present for the current slot.<br>
Unsaved changes must be for the "Discard" option to be enabled.
</body>
</html>
"""

PAGE_12 = """
<html>
<body>
To get your custom palettes into the game, you must apply your palettes to the game files.<br>
This can be done via the "Apply Palettes" option found on the toolbar or in the 
<a href="game_files_menu">Game Files</a> menu.<br><br>

This will show the Select Palettes dialog. This dialog features a character, palette, and slot selection<br>
just like the editor toolbar, as well as a sprite preview of its own. The chosen slot will be the slot<br>
that is applied to the game files for that palette.<br><br>

Applied palettes are saved and need not be re-selected each time you want to add new creations<br>
to your palette selections.
</body>
</html>
"""

PAGE_13 = """
<html>
<body>
With palettes now applied to the game files, you can launch the game and expect to see<br>
the fruits of your labor in action!<br><br>

For convenience you can launch the game from the editor with the "Launch BBCF" option<br>
in the <a href="file_menu">File</a> menu.<br><br>

If you wish to restore the game files to their original state (without using Steam),<br>
then you can use the "Restore All" and "Restore Character" options found in the 
<a href="game_files_menu">Game Files</a> menu.<br><br>

As the option names suggest, this will restore all character palette files and the<br>
currently selected character palette files to their original states, respectively.
</body>
</html>
"""

PAGE_14 = """
<html>
<body>
If you want to share your palettes with others, you can export a selection of your<br>
edit and save slots via the "Export" option found in the <a href="pal_menu">Palettes</a> menu.<br>
This will bring up a selection dialog like we have seen with "Apply Palettes", except<br>
this time it will allow us to select multiple slots per palette with a checkbox.<br><br>

Likewise, if you have downloaded or otherwise receive palettes from other folks,<br>
you can import those palettes via the "Import" option found in the <a href="pal_menu">Palettes</a> menu.<br>
Note that the importer allows for importing the export files created by the tool and also<br>
individual palette files. This is allowed so any pre-existing manually created palettes<br>
can be imported into the tool.<br><br>

When individual palette files are imported, the tool will prompt you to pick a save<br>
slot name for those files.
</body>
</html>
"""

PAGE_15 = """
<html>
<body>
That should be all you need to know! Happy palette creation!
</body>
</html>
"""

TUTORIAL_PAGES = [

    PAGE_0,
    PAGE_1,
    PAGE_2,
    PAGE_3,
    PAGE_4,
    PAGE_5,
    PAGE_6,
    PAGE_7,
    PAGE_8,
    PAGE_9,
    PAGE_10,
    PAGE_11,
    PAGE_12,
    PAGE_13,
    PAGE_14,
    PAGE_15,
]


class TutorialDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("BBCF Sprite Editor Tutorial")

        self.main_window = parent
        self.page_index = 0

        # Set up our tutorial text QLabel as interactive HTML.
        self.ui.tutorial_text.setTextFormat(QtCore.Qt.RichText)
        self.ui.tutorial_text.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.ui.tutorial_text.linkActivated.connect(self.link_clicked)

        self.ui.prev_button.clicked.connect(self.prev_page)
        self.ui.next_button.clicked.connect(self.next_page)
        self.ui.close_button.clicked.connect(self.close)

        self.load_page()

    def update_button_enable(self):
        prev_enabled = self.page_index > 0
        self.ui.prev_button.setEnabled(prev_enabled)

        next_enabled = self.page_index < len(TUTORIAL_PAGES) - 1
        self.ui.next_button.setEnabled(next_enabled)

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1

        self.load_page()

    def next_page(self):
        if self.page_index < len(TUTORIAL_PAGES) - 1:
            self.page_index += 1

        self.load_page()

    def load_page(self):
        self.update_button_enable()
        html_contents = TUTORIAL_PAGES[self.page_index]
        self.ui.tutorial_text.setText(html_contents)
        self.adjustSize()

    def link_clicked(self, link):
        action = os.path.basename(str(link)).upper()

        if action == "FILE_MENU":
            self.main_window.ui.file_menu.popup(QtGui.QCursor().pos())

        elif action == "EDIT_MENU":
            self.main_window.ui.edit_menu.popup(QtGui.QCursor().pos())

        elif action == "CHAR_SELECT":
            self.main_window.sprite_editor.selector.character.showPopup()

        elif action == "SLOT_SELECT":
            self.main_window.sprite_editor.selector.slot.showPopup()

        elif action == "PAL_SELECT":
            self.main_window.sprite_editor.selector.palette.showPopup()

        elif action == "HPL_SELECT":
            self.main_window.sprite_editor.selector.hpl_file.showPopup()

        elif action == "PAL_MENU":
            self.main_window.ui.palettes_menu.popup(QtGui.QCursor().pos())

        elif action == "GAME_FILES_MENU":
            self.main_window.ui.game_files_menu.popup(QtGui.QCursor().pos())
