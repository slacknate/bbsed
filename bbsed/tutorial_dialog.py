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
To begin, first we need to set the Steam installation directory.<br>
We can do this by going to the settings dialog from the <a href="file_menu">File</a> menu.
</body>
</html>
"""

PAGE_2 = """
<html>
<body>
Now we can select a character that we want to make a custom palette for.<br>
This can be done via the left-most <a href="char_select">dropdown</a> in the Character + Palette + Slot group.<br>
Go ahead, select a character!
</body>
</html>
"""

PAGE_3 = """
<html>
<body>
The sprites for each character are grouped by character action, which is<br>
typically associated to player input.<br><br>

Expand the first character action group as well as the "Animation" subgroup.<br>
This will show all sprite files for that character animation.<br>
Note that some character action groups will have multiple sub-groups of sprite files!
</body>
</html>
"""

PAGE_4 = """
<html>
<body>
Select the first sprite file in the "Animation" sub-group.<br><br>

A character sprite preview, as well as some new dialogs, have appeared!<br>
These dialogs are provide useful information for editing a character palette.<br><br>

The Sprite Zoom dialog shows a 2X zoom of the currently displayed<br>
sprite image centered on the cursor.<br>
Sometimes you may need to select an individual pixel, and unless<br>
you have super-vision odds are having a zoom is quite helpful for this.<br><br>

The Palette Data dialog displays the full palette for the displayed<br>
sprite image. This information is visualized as a 16x16 square of the<br>
256 colors present in the palette.<br><br>

Note that any sprite is not required to use all 256 of these colors.<br>
Most commonly any unused colors will be set to black, although some<br>
palettes set unused colors to something else.<br><br>

The first color in any palette, displayed in the Palette Data dialog at<br>
the bottom right corner, is the "transparent" color for this sprite. This color<br>
will not be displayed in game, and is how the sprites appear to have their<br>
custom shape, rather than being rectangular, in game. 
</body>
</html>
"""

PAGE_5 = """
<html>
<body>
The editor allows for separately editing each color palette, by number, that the game allows<br>
players to choose in game. This can be done via the middle <a href="pal_select">dropdown</a> in<br>
the Character + Palette + Slot group. Cycle through the list and see how the displayed<br>
palette changes.<br><br>

In this editor, each character palette also features something called "slots".<br>
A slot is just a save name for a custom palette. There exists a slot for every palette<br>
called "Edit". This slot is used when editing the current selected palette. This applies to<br>
both palettes that have yet to be saved as a slot, and palettes that have been created and<br>
saved previously.<br><br>

Note that if you have multiple save slots created for a single palette that the "Edit" slot<br>
will still be used when making changes for any of these saves. Be sure to save your work before<br>
working on a new palette!
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
are persistent if the app is closed.<br><br>

To save these changes to a save slot, use the "Save" or "Save As" options found on the<br>
toolbar or in the <a href="pal_menu">Palettes</a> menu. A save slot can be created whether a palette has active<br>
edits or is completely unchanged. Let's create a slot and save your active changes!
</body>
</html>
"""

PAGE_7 = """
<html>
<body>
Your changes have been saved as the name you chose for this palette slot when prompted.<br>
This name will now appear in the right-most <a href="slot_select">dropdown</a> and<br>
you can recall this palette to view or edit whenever you like!<br><br>

Note that slots are bound to the specific palette number selected during editing,<br>
so be sure to check all palette numbers if you cannot find a specific save slot.<br><br>

A save slot can be deleted via the "Delete" option found on the toolbar or in the 
<a href="pal_menu">Palettes</a> menu.<br>
A save slot must be actively selected for the "Delete" option to be enabled.
</body>
</html>
"""

PAGE_8 = """
<html>
<body>
Note that there are also "Copy", "Paste", and "Discard" options<br>
found in the <a href="pal_menu">Palettes</a> menu and toolbar.<br><br>

When "Copy" is activated the tool will copy the current selected palette<br>
slot. This occurs whether or not there are active changes. Both save slots<br>
and the "Edit" slot can be copied.<br><br>

When "Paste" is activated the tool will overwrite the current selected<br>
palette slot with a previously been copied palette.<br>
This will clear the palette clipboard.<br><br>

The "Discard" option will remove any active changes present in the "Edit" slot.<br>
An "Edit" slot must be actively selected and have active changes for the "Discard"<br>
option to be enabled.
</body>
</html>
"""

PAGE_9 = """
<html>
<body>
To get your custom palettes into the game, you must apply your palettes to the game files.<br>
This can be done via the "Apply Palettes" option found on the toolbar or in the 
<a href="game_files_menu">Game Files</a> menu.<br><br>

This will show the Select Palettes dialog. This dialog features a character selection and sprite<br>
preview of its own. The remaining UI elements are for selecting palettes to apply to the game files.<br><br>

If the "None" option is selected then the game version of that palette will not be replaced.<br>
Otherwise, the palette will be replaced with one created in the editor. Note that the "Edit" slot<br>
is available for choosing so you can view your changes in game before saving them if you so desire.<br><br>

The state of this dialog is saved when accepted, so palettes previously applied need not be<br>
re-selected each time you want to add new creations to your palette selections.
</body>
</html>
"""

PAGE_10 = """
<html>
<body>
With palettes now applied to the game files, you can launch the game and expect to see<br>
the fruits of your labor in action!<br><br>

For convenience you can launch the game from the editor with the "Launch BBCF" option<br>
in the <a href="file_menu">File</a> menu.
</body>
</html>
"""

# TODO: Restore All, Restore Character, Export, Import

PAGE_11 = """
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

        self.update_button_enable()
        self.load_page()

    def next_page(self):
        if self.page_index < len(TUTORIAL_PAGES) - 1:
            self.page_index += 1

        self.update_button_enable()
        self.load_page()

    def load_page(self):
        html_contents = TUTORIAL_PAGES[self.page_index]
        self.ui.tutorial_text.setText(html_contents)
        self.adjustSize()

    def link_clicked(self, link):
        action = os.path.basename(str(link)).upper()

        if action == "FILE_MENU":
            self.main_window.ui.file_menu.popup(QtGui.QCursor().pos())

        elif action == "CHAR_SELECT":
            self.main_window.sprite_editor.ui.char_select.showPopup()

        elif action == "PAL_SELECT":
            self.main_window.sprite_editor.ui.palette_select.showPopup()

        elif action == "PAL_MENU":
            self.main_window.ui.palettes_menu.popup(QtGui.QCursor().pos())

        elif action == "SLOT_SELECT":
            self.main_window.sprite_editor.ui.slot_select.showPopup()

        elif action == "GAME_FILES_MENU":
            self.main_window.ui.game_files_menu.popup(QtGui.QCursor().pos())
