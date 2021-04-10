__all__ = [

    # Constants
    "BBCF_STEAM_APP_ID",
    "SPRITE_FILE_FMT",
    "PALETTE_FILE_FMT",
    "BACKUP_PALETTE_FILE_FMT",
    "GAME_PALETTE_SUFFIX",
    "BACKUP_GAME_PALETTE_EXT",
    "GAME_PALETTE_EXT",
    "BACKUP_PALETTE_EXT",
    "DIRTY_PALETTE_EXT",
    "PALETTE_EXT",
    "SPRITE_EXT",
    "PNG_EXT",
    "PALETTE_SAVE_MARKER",
    "SLOT_NAME_EDIT",
    "PALETTE_EDIT",
    "PALETTE_SAVE",
    "CHAR_ABBR_LEN",
    "PALETTE_ID_LEN",
    "GAME_MAX_PALETTES",

    # Functions
    "block_signals",
    "temp_directory",
    "palette_id_to_number",
    "palette_number_to_id",
]

import shutil
import tempfile
import contextlib

BBCF_STEAM_APP_ID = "586140"

SPRITE_FILE_FMT = "char_{}_img.pac"
PALETTE_FILE_FMT = "char_{}_pal.pac"
BACKUP_PALETTE_FILE_FMT = "char_{}_pal.orig.pac"

GAME_PALETTE_SUFFIX = "_pal.pac"

BACKUP_GAME_PALETTE_EXT = ".orig.pac"
GAME_PALETTE_EXT = ".pac"

BACKUP_PALETTE_EXT = ".orig.hpl"
DIRTY_PALETTE_EXT = ".dirty.hpl"
PALETTE_EXT = ".hpl"
SPRITE_EXT = ".hip"
PNG_EXT = ".png"

PALETTE_SAVE_MARKER = ".save-"

SLOT_NAME_EDIT = "Edit"
PALETTE_EDIT = 1
PALETTE_SAVE = 2

CHAR_ABBR_LEN = 2
PALETTE_ID_LEN = 2
# The game only offers palettes 1-24, but there are files for 1-26? Odd.
GAME_MAX_PALETTES = 24


@contextlib.contextmanager
def block_signals(widget):
    """
    Context manager to temporarily block signals on a widget.
    Useful for resetting widgets without emitting signals that would otherwise cause error conditions.
    """
    widget.blockSignals(True)

    try:
        yield

    finally:
        widget.blockSignals(False)


@contextlib.contextmanager
def temp_directory():
    """
    Context manager to create a temp directory and delete it when the block is exited.
    Useful for our file import/export procedures.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        yield temp_dir

    finally:
        shutil.rmtree(temp_dir)


def palette_id_to_number(palette_id):
    """
    Convert a palette number to a palette ID. We ensure it is always 2 digits.
    A palette number is the prefix number that appears in HPL file names.
    A palette ID is the number we see in game and also in the tool UI.
    """
    palette_num_on_disk = int(palette_id) - 1
    return f"{palette_num_on_disk:02}"


def palette_number_to_id(palette_number):
    """
    Convert a palette number to a palette ID. We ensure it is always 2 digits.
    A palette number is the prefix number that appears in HPL file names.
    A palette ID is the number we see in game and also in the tool UI.
    """
    palette_num_in_game = int(palette_number) + 1
    return f"{palette_num_in_game:02}"
