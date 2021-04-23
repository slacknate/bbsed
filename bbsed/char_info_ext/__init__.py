__all__ = [

    # All the character data ever.
    "CHARACTER_EXT_INFO",

    # Constants used to populate our extended data in the sprite editor.
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
]

from ..char_info import *

from .util import *
from .amane import AMANE_EXT
from .arakune import ARAKUNE_EXT
from .azrael import AZRAEL_EXT
from .bang import BANG_EXT
from .bullet import BULLET_EXT
from .carl import CARL_EXT
from .izanami import IZANAMI_EXT
from .izayoi import IZAYOI_EXT

CHARACTER_EXT_INFO = {

    AMANE: AMANE_EXT,
    ARAKUNE: ARAKUNE_EXT,
    AZRAEL: AZRAEL_EXT,
    BANG: BANG_EXT,
    BULLET: BULLET_EXT,
    CARL: CARL_EXT,
    CELICA: {},
    ES: {},
    HAKUMEN: {},
    HAZAMA: {},
    HIBIKI: {},
    IRON_TAGER: {},
    IZANAMI: IZANAMI_EXT,
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
