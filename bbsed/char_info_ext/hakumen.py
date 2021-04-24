from .util import *

HAKUMEN_EXT = {

    FILTER_FILES: make_filter("pt", "rc", "tb"),

    EFFECT_FILES: {

        IGNORE_FILES: (

            "vr_white.hip",
            "vrhaef_dummy.hip",
            "vrjnef430_00.hip",
            "vrjnef430_01.hip",
            "vrjnef430_02.hip",
        ),

        GROUP_FILES: {

            # FIXME: There is no associated palette for these files. See FIXME in CELICA_EXT.
            "Slash Effects": {

                HIP_FILE_LIST: (

                    "vrhaef202_00.hip",
                    "vrhaef212_00.hip",
                    "vrhaef212_01.hip",
                    "vrhaef214_00.hip",
                    "vrhaef232_00.hip",
                    "vrhaef234_00.hip",
                    "vrhaef234_01.hip",
                    "vrhaef252_00.hip",
                    "vrhaef252_01.hip",
                    "vrhaef252_02.hip",
                    "vrhaef252_03.hip",
                    "vrhaef252_04.hip",
                    "vrhaef260_00.hip",
                    "vrhaef402_00.hip",
                    "vrhaef402_10.hip",
                    "vrhaef404_00.hip",
                    "vrhaef404_01.hip",
                    "vrhaef406_00.hip",
                    "vrhaef406_01.hip",
                    "vrhaef408_00.hip",
                    "vrhaef408_01.hip",
                ),

                PALETTE_FILE: None,
            },

            # FIXME: There is no associated palette for these files. See FIXME in CELICA_EXT.
            "Brush-strokes": {

                HIP_FILE_LIST: (

                    "vrhaef401e_00.hip",
                    "vrhaef401e_10.hip",
                    "vrhaef401_00.hip",
                    "vrhaef401_01.hip",
                    "vrhaef401_10.hip",
                    "vrhaef401_11.hip",
                    "vrhaef401_20.hip",
                    "vrhaef401_21.hip",
                    "vrhaef401_30.hip",
                    "vrhaef401_31.hip",
                    "vrhaef403_00.hip",
                    "vrhaef403_01.hip",
                    "vrhaef403_10.hip",
                    "vrhaef403_11.hip",
                    "vrhaef405_00.hip",
                    "vrhaef405_01.hip",
                    "vrhaef407_00.hip",
                    "vrhaef407_01.hip",
                    "vrhaef410_00.hip",
                    "vrhaef410_01.hip",
                    "vrhaef410_10.hip",
                    "vrhaef410_11.hip",
                ),

                PALETTE_FILE: None,
            },

            "Relius Astral": {

                HIP_FILE_LIST: (

                    "vrhaef900_00.hip",
                ),

                PALETTE_FILE: "ha{}_01.hpl",
            },

            "Unknown": {

                HIP_FILE_LIST: (

                    "vrhaef451_black.hip",
                ),

                PALETTE_FILE: "ha{}_02.hpl",
            },

            "Kokūjin Oūgi: Akumetsu": {

                HIP_FILE_LIST: (

                    "vrhaef451_fude.hip",
                ),

                PALETTE_FILE: "ha{}_02.hpl",
            },

            "Fuumajin": {

                GROUP_FILES: {

                    "Ring": {

                        HIP_FILE_LIST: (

                            "vrhaef_shotkiller.hip",
                        ),

                        PALETTE_FILE: "ha{}_01.hpl",
                    },

                    "Center": {

                        HIP_FILE_LIST: (

                            "vrhaef_power01.hip",
                        ),

                        PALETTE_FILE: "ha{}_01.hpl",
                    },
                },
            },
        },
    },
}
