__all__ = [

    # All the character data ever.
    "CHARACTER_EXT_INFO",

    # Constants used to populate our extended data in the sprite editor.
    "DEFAULT_PALETTE_FMT",
    "SPRITE_FILES",
    "EFFECT_FILES",
    "CHARACTER_STATES",
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
]

from ..char_info import *

from .constants import *
from .izayoi import IZAYOI_EXT

CHARACTER_EXT_INFO = {

    AMANE: {},
    ARAKUNE: {},
    AZRAEL: {},
    BANG: {},
    BULLET: {},
    CARL: {},
    CELICA: {},
    ES: {},
    HAKUMEN: {},
    HAZAMA: {},
    HIBIKI: {},
    IRON_TAGER: {},
    IZANAMI: {},
    IZAYOI: IZAYOI_EXT,
    JIN: {},
    JUBEI: {},
    KAGURA: {},
    KOKONOE: {},
    LITCHI: {},
    MAKOTO: {},
    MAI: {},
    NAOTO: {},
    NINE: {},
    NOEL: {},
    PLATINUM: {},
    RACHEL: {},
    RAGNA: {},
    RELIUS: {},
    SUSANOO: {},
    TAOKAKA: {},
    TSUBAKI: {},
    TERUMI: {},
    VALKENHAYNE: {},
    LAMBDA: {},
    MU: {},
    NU: {}
}
