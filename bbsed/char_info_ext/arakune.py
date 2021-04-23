from .util import *

ARAKUNE_EXT = {

    FILTER_FILES: make_filter("bn"),

    SPRITE_FILES: {

        GROUP_FILES: {

            "Relius Astral": {

                GROUP_FILES: {

                    "Character": {

                        HIP_FILE_LIST: (

                            "ar900_00.hip",
                            "ar900_01.hip",
                            "ar900_02.hip",
                        ),

                        PALETTE_FILE: "ar{}_00.hpl",
                    },

                    "Stand": {

                        HIP_FILE_LIST: (

                            "ar900_00ex00.hip",
                        ),

                        PALETTE_FILE: "ar{}_01.hpl",
                    },
                },
            },

            "Amane Astral": {

                HIP_FILE_LIST: (

                    "ar901_00.hip",
                ),

                PALETTE_FILE: "ar{}_01.hpl",
            },
        },
    },

    EFFECT_FILES: {

        GROUP_FILES: {

            "Aura": {

                HIP_FILE_LIST: (

                    "vraref000_00.hip",
                ),

                PALETTE_FILE: "ar{}_00.hpl",
            },

            "Unknown": {

                HIP_FILE_LIST: (

                    "vr_comopong00.hip",
                    "vr_comopong01.hip",
                    "vr_comopong02.hip",
                    "vr_comopong03.hip",
                    "vr_comopong04.hip",
                    "vr_comopong05.hip",
                    "vr_himedani00.hip",
                    "vr_himedani01.hip",
                    "vr_himedani02.hip",
                ),

                PALETTE_FILE: "ar{}_02.hpl",
            },

            "Negating p (web)": {

                HIP_FILE_LIST: (

                    "vraref407_00.hip",
                    "vraref407_01.hip",
                    "vraref407_02.hip",
                    "vraref407_03.hip",
                    "vraref407_90.hip",
                ),

                PALETTE_FILE: "ar{}_04.hpl",
            },

            "Bugs": {

                GROUP_FILES: {

                    "A": {

                        HIP_FILE_LIST: (

                            "vraref_spA_00.hip",
                            "vraref_spA_01.hip",
                            "vraref_spA_02.hip",
                            "vraref_spA_03.hip",
                            "vraref_spA_04.hip",
                            "vraref_spA_05.hip",
                            "vraref_spA_06.hip",
                        ),

                        PALETTE_FILE: "ar{}_02.hpl",
                    },

                    "B": {

                        HIP_FILE_LIST: (

                            "vraref_spB_00.hip",
                            "vraref_spB_01.hip",
                        ),

                        PALETTE_FILE: "ar{}_02.hpl",
                    },

                    "C": {

                        HIP_FILE_LIST: (

                            "vraref_spC_00.hip",
                            "vraref_spC_01.hip",
                            "vraref_spC_02.hip",
                            "vraref_spC_03.hip",
                            "vraref_spC_04.hip",
                            "vraref_spC_05.hip",
                            "vraref_spC_07.hip",
                            "vraref_spC_08.hip",
                            "vraref_spC_09.hip",
                        ),

                        PALETTE_FILE: "ar{}_02.hpl",
                    },

                    "D": {

                        HIP_FILE_LIST: (

                            "vraref_spD_00.hip",
                            "vraref_spD_01.hip",
                            "vraref_spD_02.hip",
                            "vraref_spD_03.hip",
                            "vraref_spD_04.hip",
                            "vraref_spD_05.hip",
                        ),

                        PALETTE_FILE: "ar{}_02.hpl",
                    },

                    "1/2/3/6D": {

                        HIP_FILE_LIST: (

                            "vraref213_00.hip",
                            "vraref213_01.hip",
                            "vraref233_00.hip",
                            "vraref233_01.hip",
                            "vraref233_02.hip",
                            "vraref233_03.hip",
                            "vraref233_04.hip",
                            "vraref233_05.hip",
                            "vraref233_06.hip",
                            "vraref233_07.hip",
                            "vraref233_08.hip",
                            "vraref233_09.hip",
                            "vraref233_10.hip",
                            "vraref233_11.hip",
                            "vraref233_12.hip",
                            "vraref233_13.hip",
                            "vraref253_00.hip",
                            "vraref253_01.hip",
                            "vraref253_02.hip",
                            "vraref253_03.hip",
                            "vraref253_04.hip",
                            "vraref253_05.hip",
                            "vraref253_06.hip",
                            "vraref253_07.hip",
                            "vraref253_08.hip",
                            "vraref253_09.hip",
                            "vraref253_10.hip",
                            "vraref253_11.hip",
                            "vraref253_12.hip",
                            "vraref253_13.hip",
                            "vraref430_00.hip",
                        ),

                        PALETTE_FILE: "ar{}_00.hpl",
                    },

                    "F equals": {

                        HIP_FILE_LIST: (

                            "vraref441_00.hip",
                            "vraref441_01.hip",
                            "vraref441_02.hip",
                            "vraref441_03.hip",
                        ),

                        PALETTE_FILE: "ar{}_02.hpl",
                    },

                    "Permutation": {

                        HIP_FILE_LIST: (

                            "vraref404_00.hip",
                            "vraref404_01.hip",
                        ),

                        PALETTE_FILE: "ar{}_02.hpl",
                    },

                    "Unknown": {

                        HIP_FILE_LIST: (

                            "vrarefsp_00.hip",
                        ),

                        # Is this the correct palette?
                        PALETTE_FILE: "ar{}_02.hpl",
                    },
                },
            },
        },
    },
}
