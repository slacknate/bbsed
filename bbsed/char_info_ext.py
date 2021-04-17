__all__ = [

    # All the character data ever.
    "CHARACTER_EXT_INFO",

    # Constants used to make out extended data in the sprite editor.
    "DEFAULT_PALETTE_FILE",
    "SPRITE_PALETTE_MAP",
    "EFFECT_PALETTE_MAP",
    "CHARACTER_STATES",
    "HIP_FILE_LIST",
    "PALETTE_FILE",
    "STATE_DEFINITION",
    "STATE_INITIAL",
    "STATE_CHANGE",
    "SWAP_COLORS",
    "SWAP_PALETTES",
    "SWAP_INDICES",
]

from .char_info import *

DEFAULT_PALETTE_FILE = 0
SPRITE_PALETTE_MAP = 1
EFFECT_PALETTE_MAP = 2
CHARACTER_STATES = 3

HIP_FILE_LIST = 0
PALETTE_FILE = 1
STATE_DEFINITION = 2
STATE_INITIAL = 3
STATE_CHANGE = 4

SWAP_COLORS = 0
SWAP_PALETTES = 1
SWAP_INDICES = 2

# TODO: izanami also has palette swaps because of her time stops. we should implement her next

_IZAYOI_EXT = {

    DEFAULT_PALETTE_FILE: "iz{}_00.hpl",

    SPRITE_PALETTE_MAP: {

        "Transform Intro": {

            HIP_FILE_LIST: (

                "iz600_00.hip",
                "iz600_01.hip",
                "iz600_02.hip",
                "iz600_02ex00.hip",
                "iz600_03.hip",
                "iz600_03ex00.hip",
                "iz600_04.hip",
                "iz600_04ex00.hip",
                "iz600_04ex01.hip",
                "iz600_05.hip",
                "iz600_05ex00.hip",
                "iz600_05ex01.hip",
                "iz600_06.hip",
                "iz600_06ex00.hip",
                "iz600_06ex01.hip",
                "iz600_07.hip",
                "iz600_07ex00.hip",
                "iz600_07ex01.hip",
                "iz600_07ex02.hip",
                "iz600_07ex03.hip",
                "iz600_07ex04.hip"
            ),

            PALETTE_FILE: "iz{}_03.hpl"
        },

        "Relius Astral": {

            HIP_FILE_LIST: (

                "iz900_00.hip",
            ),

            PALETTE_FILE: "iz{}_00.hpl"
        },

        "Amane Astral": {

            HIP_FILE_LIST: (

                "iz901_00.hip",
            ),

            PALETTE_FILE: "iz{}_00.hpl"
        },
    },

    EFFECT_PALETTE_MAP: {

        "Normal Actions": {

            HIP_FILE_LIST: (

                "vrizef202_00.hip",
                "vrizef202_01.hip",
                "vrizef203_00.hip",
                "vrizef204_00.hip",
                "vrizef210_f04.hip",
                "vrizef211_f09.hip",
                "vrizef212_f06.hip",
                "vrizef212_f07.hip",
                "vrizef232_00.hip",
                "vrizef232_01.hip",
                "vrizef232_02.hip",
                "vrizef233_00.hip",
                "vrizef233_01.hip",
                "vrizef233_02.hip",
                "vrizef234_00.hip",
                "vrizef235_00.hip",
                "vrizef235_01.hip",
                "vrizef252_00.hip",
                "vrizef252_01.hip",
                "vrizef254_00.hip",
            ),

            # Do we need to care about Gain Art?
            PALETTE_FILE: "iz{}_01.hpl"
        },

        "Side Blade Effects": {

            HIP_FILE_LIST: (

                "vrizef213_00.hip",
                "vrizef213_01.hip",
                "vrizef213_02.hip",
                "vrizef213_03.hip",
                "vrizef253_00.hip",
                "vrizef253_01.hip",
                "vrizef253_02.hip",
                "vrizef253_03.hip",
                "vrizef253_04.hip",
                "vrizef440_40.hip",
                "vrizef440_41.hip",
                "vrizef440_42.hip",
                "vrizef440_43.hip",
                "vrizef440_44.hip",
                "vrizef440_45.hip",
            ),

            PALETTE_FILE: "iz{}_02.hpl"
        },

        "Special Actions": {

            HIP_FILE_LIST: (

                "vrizef_402_00.hip",
                "vrizef_402_01.hip",
                "vrizef_402_02.hip",
                "vrizef_402_03.hip",
                "vrizef_402_04.hip",
                "vrizef_402_05.hip",
                "vrizef_402_10.hip",
                "vrizef_402_11.hip",
                "vrizef_402_12.hip",
                "vrizef_402_13.hip",
                "vrizef_402_14.hip",
                "vrizef_402_15.hip",
                "vrizef_404_00.hip",
                "vrizef_404_01.hip",
                "vrizef_404_02.hip",
                "vrizef_404_03.hip",
                "vrizef_404_04.hip",
                "vrizef_404_05.hip",
                "vrizef_405_01.hip",
                "vrizef_405_02.hip",
                "vrizef_405_03.hip",
                "vrizef_405_04.hip",
                "vrizef_405_05.hip",
                "vrizef_406_00.hip",
                "vrizef_406_01.hip",
                "vrizef412_00.hip",
                "vrizef_413_00.hip",
                "vrizef_413_01.hip",
                "vrizef_413_02.hip",
                "vrizef_413_03.hip",
                "vrizef_413_04.hip",
                "vrizef_413_11.hip",
                "vrizef_413_12.hip",
                "vrizef_413_13.hip",
                "vrizef_413_14.hip",
                "vrizef_413_15.hip",
                "vrizef_413_21.hip",
                "vrizef_413_22.hip",
                "vrizef_413_23.hip",
                "vrizef_413_24.hip",
                "vrizef440_30.hip",
                "vrizef440_31.hip",
                "vrizef400swd00.hip",
                "vrizef400swd01.hip",
            ),

            # We set the initial palette for Gain Art being inactive.
            PALETTE_FILE: "iz{}_04.hpl"
        },

        "Banshee Lancer": {

            HIP_FILE_LIST: (

                "vrizef440_00.hip",
                "vrizef440_01.hip",
                "vrizef440_02.hip",
                "vrizef440_03.hip",
                "vrizef440_10.hip",
                "vrizef440_11.hip",
                "vrizef440_12.hip",
                "vrizef440_13.hip",
                "vrizef440_20.hip",
                "vrizef440_21.hip",
                "vrizef440_22.hip",
                "vrizef440_23.hip",
            ),

            PALETTE_FILE: "iz{}_02.hpl"
        },

        "Justice Phorizor": {

            HIP_FILE_LIST: (

                "vrizef430swd00.hip",
                "vrizef430swd_env.hip"
            ),

            PALETTE_FILE: "iz{}_06.hpl"
        },

        "Slaver Trans-Am (Summons)": {

            HIP_FILE_LIST: (

                "vrizef431_00.hip",
            ),

            PALETTE_FILE: "iz{}_00.hpl"
        },

        # FIXME: WHAT ARE THESE??
        "Unknown": {

            HIP_FILE_LIST: (

                "vrizef440_50.hip",
                "vrizef440_51.hip",
                "vrizef440_52.hip",

                "vrizef601_09.hip",
                "vrizef601_10.hip",
                "vrizef601_11.hip",
                "vrizef601_18.hip",
                "vrizef601_19.hip",

                "vrizef_408_00.hip",
                "vrizef_408_01.hip",
                "vrizef_408_02.hip",
            ),

            # FIXME: this group is a smattering of files so this palette has to be wrong
            PALETTE_FILE: "iz{}_01.hpl"
        }
    },

    CHARACTER_STATES: {

        # This will result in a Inactive being the first displayed choice.
        STATE_DEFINITION: ("Gain Art", ("Inactive", "Active")),

        STATE_INITIAL: "Inactive",

        STATE_CHANGE: {

            SWAP_COLORS: (

                {
                    PALETTE_FILE: "iz{}_00.hpl",
                    SWAP_INDICES: (

                        ((10, 11), (13, 11)),
                        ((11, 11), (14, 11)),
                        ((12, 11), (15, 11)),
                    ),
                },
            ),

            SWAP_PALETTES: (

                ("iz{}_04.hpl", "iz{}_05.hpl"),
            ),
        },
    },
}

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
    IZAYOI: _IZAYOI_EXT,
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
