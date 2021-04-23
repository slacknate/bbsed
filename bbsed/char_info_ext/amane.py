from .util import *

AMANE_EXT = {

    FILTER_FILES: make_filter("kk", "rg"),

    EFFECT_FILES: {

        IGNORE_FILES: (

            "vrdmy.hip",
            "vr_yugami.hip",
        ),

        GROUP_FILES: {

            "Troupe Intro": {

                HIP_FILE_LIST: (

                    "vramef600_00.hip",
                    "vramef600_01.hip",
                    "vramef600_02.hip",
                    "vramef600_03.hip",
                    "vramef600_04.hip",
                    "vramef600_05.hip",
                    "vramef600_06.hip",
                    "vramef600_07.hip",
                    "vramef600_08.hip",
                    "vramef600_09.hip",
                ),

                PALETTE_FILE: "am{}_02.hpl",
            },

            "Troupe Outro ??": {

                HIP_FILE_LIST: (

                    "vramef610_00.hip",
                    "vramef610_01.hip",
                ),

                PALETTE_FILE: "am{}_02.hpl",
            },

            # No idea what this is for :|
            "Unknown": {

                HIP_FILE_LIST: (

                    "vramef430_00.hip",
                    "vramef430_01.hip",
                    "vramef430_02.hip",
                    "vramef430_03.hip",
                    "vramef430_04.hip",
                    "vramef430_05.hip",
                    "vramef430_06.hip",
                    "vramef430_07.hip",
                    "vramef430_08.hip",
                    "vramef430_09.hip",
                    "vramef430_10.hip",
                ),

                PALETTE_FILE: "am{}_01.hpl",
            },

            # Is this correct? I believe it is but we may need to re-name this group.
            "Kyouryuu Tokkou: Seijyuu Rensoukyaku": {

                HIP_FILE_LIST: (

                    "vram440_hiteff00.hip",
                    "vram440_hiteff01.hip",
                    "vram440_hiteff02.hip",
                    "vram440_hiteff03.hip",
                    "vram440_hiteff04.hip",
                ),

                PALETTE_FILE: "am{}_03.hpl",
            },

            "Jyatoku Meika: Gouha Houyou": {

                HIP_FILE_LIST: (

                    "vramef450_00.hip",
                    "vramef450_01.hip",
                    "vramef450_02.hip",
                    "vramef450_03.hip",
                    "vramef450_04.hip",
                    "vramef450_05.hip",
                    "vramef450_06.hip",
                    "vramef450_07.hip",
                    "vramef450_08.hip",
                    "vramef450_09.hip",
                    "vramef450_10.hip",
                ),

                PALETTE_FILE: "am{}_00.hpl",
            },

            "Special Actions": {

                HIP_FILE_LIST: (

                    "vramef402_00.hip",
                    "vramef402_01.hip",
                    "vramef402_02.hip",
                    "vramef402_03.hip",
                    "vramef402_10.hip",
                    "vramef402_11.hip",
                    "vramef402_20.hip",
                    "vramef402_21.hip",
                    "vramef402_22.hip",
                    "vramef406_00.hip",
                    "vramef406_01.hip",
                    "vramef406_02.hip",
                    "vramef406_03.hip",
                    "vramef406_04.hip",
                    "vramef406_05.hip",
                    "vramef406_10.hip",
                    "vramef406_11.hip",
                    "vramef406_90.hip",
                ),

                PALETTE_FILE: "am{}_00.hpl",
            },

            "Standard Throws": {

                HIP_FILE_LIST: (

                    "vramef311_00.hip",
                ),

                PALETTE_FILE: "am{}_00.hpl",
            },

            "Drills": {

                HIP_FILE_LIST: (

                    "vramef213_00.hip",
                    "vramef401_00.hip",
                    "vramef401_01.hip",
                    "vramef401_02.hip",
                    "vramef401_03.hip",
                    "vramef401_04.hip",
                    "vramef431_00.hip",
                    "vramef431_01.hip",
                    "vramef431_02.hip",
                    "vramef431_03.hip",
                    "vramef431_04.hip",
                    "vramef431_10.hip",
                    "vramef431_11.hip",
                    "vramef431_12.hip",
                    "vramef431_13.hip",
                    "vramef431_14.hip",
                    "vramef431_15.hip",
                    "vramef431_16.hip",
                    "vramef431_17.hip",
                    "vramef431_18.hip",
                    "vramef431_19.hip",
                    "vramef431_20.hip",
                    "vramef431_21.hip",
                ),

                PALETTE_FILE: "am{}_00.hpl",
            },
        },
    },
}
