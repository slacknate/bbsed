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
    "PALETTE_EXT",
    "SPRITE_EXT",
    "PNG_EXT",
    "HASH_EXT",
    "PALETTE_EDIT_MARKER",
    "PALETTE_SAVE_MARKER",
    "EDIT_INTERNAL_NAME",
    "SLOT_NAME_NONE",
    "SLOT_NAME_EDIT",
    "PALETTE_NONE",
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
    "get_hash_path",
    "hash_file",
]

import shutil
import hashlib
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
PALETTE_EXT = ".hpl"
SPRITE_EXT = ".hip"
PNG_EXT = ".png"
HASH_EXT = ".sha256"

PALETTE_EDIT_MARKER = ".edit"
PALETTE_SAVE_MARKER = ".save-"

EDIT_INTERNAL_NAME = "==EDIT=="

SLOT_NAME_NONE = "None"
SLOT_NAME_EDIT = "Edit"
PALETTE_NONE = 0
PALETTE_EDIT = 1
PALETTE_SAVE = 2

CHAR_ABBR_LEN = 2
PALETTE_ID_LEN = 2
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


def hash_file(full_path):
    """
    Return the SHA-256 hash of the given file.
    """
    hpl_hash = hashlib.sha256()

    with open(full_path, "rb") as hpl_fp:
        hpl_hash.update(hpl_fp.read())

    return hpl_hash.hexdigest()


def get_hash_path(full_path):
    """
    Get the hash path for the given file.
    We just stick our defined hash extension on the end of the path.
    This way we also maintain compatibility with our pathing module.
    """
    return full_path + HASH_EXT
