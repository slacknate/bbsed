from .util import *

BANG_EXT = {

    FILTER_FILES: make_filter("lc", "pt"),

    SPRITE_FILES: {

        GROUP_FILES: {

            "Seals (Astral)": {

                HIP_FILE_LIST: (

                    "bnef611_00.hip",
                    "bnef611_01.hip",
                    "bnef611_02.hip",
                    "bnef611_03.hip",
                    "bnef611_10.hip",
                    "bnef611_11.hip",
                    "bnef611_12.hip",
                    "bnef611_13.hip",
                ),

                PALETTE_FILE: "bn{}_02.hpl",
            },
        },
    },

    EFFECT_FILES: {

        IGNORE_FILES: (

            "vrbnef_dummy.hip",
            "vref_env.hip",
            "vr_white.hip",
        ),

        GROUP_FILES: {

            "Projectiles": {

                HIP_FILE_LIST: (

                    "vrbnef406_000.hip",
                    "vrbnef406_001.hip",
                    "vrbnef406_002.hip",
                    "vrbnef406_003.hip",
                    "vrbnef406_004.hip",
                    "vrbnef406_005.hip",
                    "vrbnef406_006.hip",
                    "vrbnef406_007.hip",
                    "vrbnef406_008.hip",
                    "vrbnef406_009.hip",
                    "vrbnef406_010.hip",
                    "vrbnef406_011.hip",
                    "vrbnef406_090.hip",
                ),

                PALETTE_FILE: "bn{}_00.hpl",
            },

            "Bumper": {

                GROUP_FILES: {

                    "Nail": {

                        HIP_FILE_LIST: (

                            "vrbnef407_001.hip",
                            "vrbnef407_002.hip",
                            "vrbnef407_003.hip",
                            "vrbnef407_004.hip",
                            "vrbnef407_005.hip",
                            "vrbnef407_006.hip",
                            "vrbnef407_007.hip",
                        ),

                        PALETTE_FILE: "bn{}_00.hpl",
                    },

                    "Sigil": {

                        HIP_FILE_LIST: (

                            "vrbnef407_90.hip",
                        ),

                        PALETTE_FILE: "bn{}_04.hpl",
                    },
                },
            },

            "Web": {

                HIP_FILE_LIST: (

                    "vrbnef406_090.hip",
                ),

                PALETTE_FILE: "bn{}_00.hpl",
            },

            "Hit Effects": {

                HIP_FILE_LIST: (

                    "vrbnef203_00.hip",
                    "vrbnef203_10.hip",
                    "vrbnef203_11.hip",
                    "vrbnef203_12.hip",
                    "vrbnef203_13.hip",
                    "vrbnef213_00.hip",
                    "vrbnef213_10.hip",
                    "vrbnef213_11.hip",
                    "vrbnef213_12.hip",
                    "vrbnef213_13.hip",
                    "vrbnef213_14.hip",
                    "vrbnef233_00.hip",
                    "vrbnef233_10.hip",
                    "vrbnef233_11.hip",
                    "vrbnef233_12.hip",
                    "vrbnef233_13.hip",
                    "vrbnef233_14.hip",
                    "vrbnef253_00.hip",
                    "vrbnef253_10.hip",
                    "vrbnef253_11.hip",
                    "vrbnef253_12.hip",
                    "vrbnef253_13.hip",
                    "vrbnef253_14.hip",
                    "vrbnef404_00.hip",
                    "vrbnef404_01.hip",
                    "vrbnef404_02.hip",
                    "vrbnef404_03.hip",
                    "vrbnef404_04.hip",
                    "vrbnef404_05.hip",
                    "vrbnef404_06.hip",
                    "vrbnef404_07.hip",
                    "vrbnef405_00.hip",
                    "vrbnef405_01.hip",
                    "vrbnef405_02.hip",
                    "vrbnef405_03.hip",
                    "vrbnef405_04.hip",
                    "vrbnef405_05.hip",
                    "vrbnef410_00.hip",
                    "vrbnef410_01.hip",
                    "vrbnef410_02.hip",
                    "vrbnef410_03.hip",
                    "vrbnef410_04.hip",
                ),

                PALETTE_FILE: "bn{}_01.hpl",
            },

            "Bang's Dancing Petal Storm": {

                GROUP_FILES: {

                    "Shuriken": {

                        HIP_FILE_LIST: (

                            "vrbnef440_00.hip",
                            "vrbnef440_01.hip",
                            "vrbnef440_10.hip",
                            "vrbnef440_20.hip",
                        ),

                        PALETTE_FILE: "bn{}_00.hpl",
                    },

                    "Bomb": {

                        HIP_FILE_LIST: (

                            "vrbnef440_30.hip",
                        ),

                        PALETTE_FILE: "bn{}_04.hpl",
                    },
                },
            },

            "Shishigami-style Forbidden Technique: 'The Ultimate Bang'": {

                GROUP_FILES: {

                    "Closeup": {

                        HIP_FILE_LIST: (

                            "vrbnef450_face00.hip",
                            "vrbnef450_face01.hip",
                            "vrbnef450_face02.hip",
                        ),

                        PALETTE_FILE: "bn{}_02.hpl",
                    },

                    "Nail": {

                        HIP_FILE_LIST: (

                            "vrbnef450_kugi.hip",
                        ),

                        PALETTE_FILE: "bn{}_00.hpl",
                    },

                    "Door": {

                        HIP_FILE_LIST: (

                            "vrbnef450_00.hip",
                        ),

                        PALETTE_FILE: "bn{}_04.hpl",
                    },

                    "Hit Effect": {

                        HIP_FILE_LIST: (

                            "vrbnef450_90.hip",
                            "vrbnef450_91.hip",
                        ),

                        PALETTE_FILE: "bn{}_05.hpl",
                    },
                },
            },

            "FuRinKaZan": {

                GROUP_FILES: {

                    "Closeup": {

                        HIP_FILE_LIST: (

                            "vrbnef432_20.hip",
                        ),

                        PALETTE_FILE: "bn{}_00.hpl",
                    },

                    "Seals": {

                        HIP_FILE_LIST: (

                            "vrbnef432_50.hip",
                            "vrbnef432_51.hip",
                            "vrbnef432_52.hip",
                            "vrbnef432_53.hip",
                            "vrbnef432_90.hip",
                        ),

                        PALETTE_FILE: "bn{}_02.hpl",
                    },

                    "Unknown": {

                        HIP_FILE_LIST: (

                            "vrbnef432_21.hip",
                        ),

                        PALETTE_FILE: "bn{}_00.hpl",
                    },
                },
            },

            "Bang's Steel Rain": {

                HIP_FILE_LIST: (

                    "vrbnef431_000.hip",
                    "vrbnef431_001.hip",
                ),

                PALETTE_FILE: "bn{}_00.hpl",
            },

            "Secret Technique: Bang's Pulverizing Blast Jutsu (Teleport Smear)": {

                HIP_FILE_LIST: (

                    "vrbnef411_00.hip",
                    "vrbnef411_01.hip",
                    "vrbnef411_02.hip",
                    "vrbnef411_03.hip",
                    "vrbnef411_04.hip",
                ),

                PALETTE_FILE: "bn{}_00.hpl",
            },
        },
    },
}
