__all__ = [

    # Constants
    "BBCF_STEAM_APP_ID",
    "STEAM_PROCESS_NAME",
    "LOCK_FILE_EXT",
    "GAME_SPRITE_FILE_FMT",
    "GAME_PALETTE_FILE_FMT",
    "GAME_EFFECT_FILE_FMT",
    "GAME_COLLISION_FILE_FMT",
    "PALETTE_ID_FMT",
    "EFFECT_IMG_PREFIX",
    "BACKUP_GAME_PALETTE_EXT",
    "GAME_PALETTE_EXT",
    "BACKUP_PALETTE_EXT",
    "PALETTE_EXT",
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
    "iter_palettes",
    "palette_number_to_id",
    "get_hash_path",
    "hash_file",
    "steam_running",
    "create_lock",
    "delete_lock",
    "owns_lock",
    "check_lock",
]

import os
import shutil
import hashlib
import tempfile
import contextlib

import psutil

BBCF_STEAM_APP_ID = "586140"
STEAM_PROCESS_NAME = "steam.exe"
APP_PROCESS_NAME = "bbsed.exe"
SOURCE_PROCESS_NAME = "python.exe"

LOCK_FILE_EXT = ".lock"

GAME_SPRITE_FILE_FMT = "char_{}_img.pac"
GAME_PALETTE_FILE_FMT = "char_{}_pal.pac"
GAME_EFFECT_FILE_FMT = "char_{}_vri.pac"
GAME_COLLISION_FILE_FMT = "char_{}_col.pac"

PALETTE_ID_FMT = "{:02}"
EFFECT_IMG_PREFIX = "vr{}ef"

BACKUP_GAME_PALETTE_EXT = ".orig.pac"
GAME_PALETTE_EXT = ".pac"

BACKUP_PALETTE_EXT = ".orig.hpl"
PALETTE_EXT = ".hpl"

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


def iter_palettes():
    """
    Iterate our total possile palettes.
    We yield both the palette ID and palette number so
    we have access to both values wherever we need to iterate.
    """
    for palette_num in range(GAME_MAX_PALETTES):
        palette_id = palette_num + 1

        yield PALETTE_ID_FMT.format(palette_id), PALETTE_ID_FMT.format(palette_num)


def palette_number_to_id(palette_number):
    """
    Convert a palette number to a palette ID. We ensure it is always 2 digits.
    A palette number is the prefix number that appears in HPL file names.
    A palette ID is the number we see in game and also in the tool UI.
    """
    palette_num_in_game = int(palette_number) + 1
    return PALETTE_ID_FMT.format(palette_num_in_game)


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


def steam_running():
    """
    Helper to check if Steam is running.
    Launching Steam as a subprocess seems to cause problems in the app so
    we require starting it separately and then allow for just launching BBCF within the app.
    """
    for proc in psutil.process_iter():
        try:
            if proc.name() == STEAM_PROCESS_NAME:
                return True

        # If we cannot get the process name just ignore it.
        # This does not occur for Steam as far as I can tell.
        except psutil.AccessDenied:
            pass

    return False


def create_lock(lock_file):
    """
    Create a lock file at the given location.
    We simply write the pid of this process to the lock file
    so other BBCF Sprite Editor instances can determine the owner of the lock.
    """
    with open(lock_file, "w") as lock_fp:
        lock_fp.write(str(os.getpid()))


def delete_lock(lock_file):
    """
    Delete a lock file at the given location.
    """
    os.remove(lock_file)


def owns_lock(lock_file):
    """
    Determine if the given lock is owned by this BBCF Sprite Editor process.
    If the file does not exist or does not contain an integer value we assume
    that this process does not own the lock.
    If the PID described by the lock file matches the current PID then we own it.
    """
    owns = False

    if not os.path.exists(lock_file):
        return owns

    with open(lock_file, "r") as lock_fp:
        try:
            pid = int(lock_fp.read())

        except ValueError:
            return owns

    return pid == os.getpid()


def check_lock(lock_file):
    """
    Determine if the given lock file is valid.
    We consider it valid if it was created by a BBCF Sprite Editor process that still exists.
    """
    valid = False

    if not os.path.exists(lock_file):
        return valid

    with open(lock_file, "r") as lock_fp:
        try:
            pid = int(lock_fp.read())

        except ValueError:
            return valid

    # If the lock file is PID is an existing process and that process
    # is our app name then it is a valid lock file and should be left alone.
    if psutil.pid_exists(pid):
        proc = psutil.Process(pid)

        try:
            if proc.name() in (APP_PROCESS_NAME, SOURCE_PROCESS_NAME):
                valid = True

        # If we cannot get the process name just ignore it.
        # This will not occur for bbsed.exe or python.exe.
        except psutil.AccessDenied:
            pass

    return valid
