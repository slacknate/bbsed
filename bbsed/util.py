__all__ = [

    # Constants
    "BBCF_STEAM_APP_ID",
    "IMAGE_FILE_FMT",
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
    "CHAR_ABBR_LEN",

    # Functions
    "block_signals",
    "temp_directory",
]

import shutil
import tempfile
import contextlib

BBCF_STEAM_APP_ID = "586140"

IMAGE_FILE_FMT = "char_{}_img.pac"
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

CHAR_ABBR_LEN = 2


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
