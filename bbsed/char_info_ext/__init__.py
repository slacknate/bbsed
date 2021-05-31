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
    "FILE_OVERRIDE",
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
from .celica import CELICA_EXT
from .es import ES_EXT
from .hakumen import HAKUMEN_EXT
from .hazama import HAZAMA_EXT
from .hibiki import HIBIKI_EXT
from .izanami import IZANAMI_EXT
from .izayoi import IZAYOI_EXT
from .jin import JIN_EXT
from .jubei import JUBEI_EXT
from .kagura import KAGURA_EXT
from .kokonoe import KOKONOE_EXT
from .lam import LAMBDA_EXT
from .litchi import LITCHI_EXT
from .mai import MAI_EXT
from .makoto import MAKOTO_EXT
from .mu import MU_EXT
from .naoto import NAOTO_EXT
from .nine import NINE_EXT
from .noel import NOEL_EXT
from .nu import NU_EXT
from .platinum import PLATINUM_EXT
from .rachel import RACHEL_EXT
from .ragna import RAGNA_EXT
from .relius import RELIUS_EXT
from .susanoo import SUSANOO_EXT
from .tager import TAGER_EXT
from .taokaka import TAOKAKA_EXT
from .terumi import TERUMI_EXT
from .tsubaki import TSUBAKI_EXT
from .valkenhayne import VALKENHAYNE_EXT

CHARACTER_EXT_INFO = {

    AMANE: AMANE_EXT,
    ARAKUNE: ARAKUNE_EXT,
    AZRAEL: AZRAEL_EXT,
    BANG: BANG_EXT,
    BULLET: BULLET_EXT,
    CARL: CARL_EXT,
    CELICA: CELICA_EXT,
    ES: ES_EXT,
    HAKUMEN: HAKUMEN_EXT,
    HAZAMA: HAZAMA_EXT,
    HIBIKI: HIBIKI_EXT,
    IRON_TAGER: TAGER_EXT,
    IZANAMI: IZANAMI_EXT,
    IZAYOI: IZAYOI_EXT,
    JIN: JIN_EXT,
    JUBEI: JUBEI_EXT,
    KAGURA: KAGURA_EXT,
    KOKONOE: KOKONOE_EXT,
    LITCHI: LITCHI_EXT,
    MAKOTO: MAKOTO_EXT,
    MAI: MAI_EXT,
    NAOTO: NAOTO_EXT,
    NINE: NINE_EXT,
    NOEL: NOEL_EXT,
    PLATINUM: PLATINUM_EXT,
    RACHEL: RACHEL_EXT,
    RAGNA: RAGNA_EXT,
    RELIUS: RELIUS_EXT,
    SUSANOO: SUSANOO_EXT,
    TAOKAKA: TAOKAKA_EXT,
    TSUBAKI: TSUBAKI_EXT,
    TERUMI: TERUMI_EXT,
    VALKENHAYNE: VALKENHAYNE_EXT,
    LAMBDA: LAMBDA_EXT,
    MU: MU_EXT,
    NU: NU_EXT
}
