__all__ = [

    "DEFAULT_PALETTE_FMT",
    "SPRITE_FILES",
    "EFFECT_FILES",
    "CHARACTER_STATES",
    "FILTER_FILES",
    "IGNORE_FILES",
    "GROUP_FILES",
    "HIP_FILE_LIST",
    "PALETTE_FILE",
    "STATE_DEFINITION",
    "STATE_INITIAL",
    "STATE_CHANGE",
    "SWAP_COLORS",
    "SWAP_PALETTES",
    "SWAP_INDICES",

    "make_filter",
]

import re

DEFAULT_PALETTE_FMT = "{}{{}}_00.hpl"

SPRITE_FILES = 1
EFFECT_FILES = 2
CHARACTER_STATES = 3

FILTER_FILES = 0
IGNORE_FILES = 1
GROUP_FILES = 2
HIP_FILE_LIST = 3
PALETTE_FILE = 4
STATE_DEFINITION = 5
STATE_INITIAL = 6
STATE_CHANGE = 7

SWAP_COLORS = 0
SWAP_PALETTES = 1
SWAP_INDICES = 2


def make_filter(*characters):
    """
    Helper to create a filter function to remove files from the list of sprite files to be displayed to the user.
    Used to for bulk removal of files that match a pattern.
    """
    if len(characters) == 0:
        raise ValueError("Must provide at least one character!")

    elif len(characters) == 1:
        char_selection = characters[0]

    else:
        char_selection = "(" + "|".join(characters) + ")"

    filter_regex = re.compile(f"^{char_selection}.+")
    return lambda hip_file: filter_regex.search(hip_file) is None
