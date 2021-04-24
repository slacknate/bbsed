from .util import *

ES_EXT = {

    FILTER_FILES: make_filter("rg"),

    SPRITE_FILES: {

        IGNORE_FILES: (

            "esef600_screen.hip",
        ),

        GROUP_FILES: {

            "Sword Summon Intro": {

                HIP_FILE_LIST: (

                    "esef611_sword00.hip",
                ),

                PALETTE_FILE: "es{}_00.hpl",
            },

            "Glow Effects": {

                HIP_FILE_LIST: (

                    "esef431_00.hip",
                    "esef431_01.hip",
                    "esef431_02.hip",
                    "esef431_03.hip",
                    "esef431_04.hip",
                    "esef431_05.hip",
                    "esef431_11.hip",
                    "esef431_12.hip",
                    "esef431_13.hip",
                    "esef431_14.hip",
                    "esef431_15.hip",
                    "esef431_20.hip",
                    "esef600_00.hip",
                    "esef601_00.hip",
                    "esef601_01.hip",
                    "esef601_02.hip",
                    "esef611_07.hip",
                    "esef611_08.hip",
                    "esef611_09.hip",
                    "esef611_10.hip",
                    "esef611_11.hip",
                    "esef611_sword01.hip",
                    "esef611_sword02.hip",
                    "esef611_sword03.hip",
                    "esef611_sword04.hip",
                ),

                PALETTE_FILE: "es{}_04.hpl",
            },

            "Character Emblems": {

                HIP_FILE_LIST: (

                    "esef_emb_am.hip",
                    "esef_emb_ar.hip",
                    "esef_emb_az.hip",
                    "esef_emb_bl.hip",
                    "esef_emb_bn.hip",
                    "esef_emb_ca.hip",
                    "esef_emb_ce.hip",
                    "esef_emb_es.hip",
                    "esef_emb_ha.hip",
                    "esef_emb_hb.hip",
                    "esef_emb_hz.hip",
                    "esef_emb_iz.hip",
                    "esef_emb_jb.hip",
                    "esef_emb_jn.hip",
                    "esef_emb_kg.hip",
                    "esef_emb_kk.hip",
                    "esef_emb_lc.hip",
                    "esef_emb_ma.hip",
                    "esef_emb_mi.hip",
                    "esef_emb_mk.hip",
                    "esef_emb_mu.hip",
                    "esef_emb_no.hip",
                    "esef_emb_nt.hip",
                    "esef_emb_ny.hip",
                    "esef_emb_ph.hip",
                    "esef_emb_pt.hip",
                    "esef_emb_rc.hip",
                    "esef_emb_rg.hip",
                    "esef_emb_rl.hip",
                    "esef_emb_rm.hip",
                    "esef_emb_su.hip",
                    "esef_emb_tb.hip",
                    "esef_emb_tg.hip",
                    "esef_emb_tk.hip",
                    "esef_emb_tm.hip",
                    "esef_emb_vh.hip",
                ),

                PALETTE_FILE: "es{}_03.hpl",
            },
        },
    },

    EFFECT_FILES: {

        GROUP_FILES: {

            # FIXME: not sure if the palette for these is correct
            "Unknown": {

                HIP_FILE_LIST: (

                    "vresef201_00.hip",
                    "vresef202_00.hip",
                    "vresef202_01.hip",
                    "vresef211_00.hip",
                    "vresef231_00.hip",
                    "vresef232_00.hip",
                    "vresef232_01.hip",
                    "vresef235_00.hip",
                    "vresef235_01.hip",
                    "vresef235_02.hip",
                    "vresef235_03.hip",
                    "vresef235_04.hip",
                    "vresef251_00.hip",
                    "vresef251_10.hip",
                    "vresef252_00.hip",
                    "vresef340_00.hip",
                    "vresef400_00.hip",
                    "vresef400_01.hip",
                    "vresef400_10.hip",
                    "vresef400_11.hip",
                    "vresef401_00.hip",
                    "vresef401_01.hip",
                    "vresef401_10.hip",
                    "vresef402_00.hip",
                    "vresef402_01.hip",
                    "vresef404_00.hip",
                    "vresef404_01.hip",
                    "vresef404_02.hip",
                    "vresef615_whitesord.hip",
                ),

                PALETTE_FILE: "es{}_01.hpl",
            },

            # FIXME: better name, maybe group with the first glow group?
            "Other Glow Effects": {

                HIP_FILE_LIST: (

                    "vresef432_00.hip",
                    "vresef432_01.hip",
                    "vresef432_02.hip",
                    "vresef432_03.hip",
                    "vresef432_04.hip",
                    "vresef432_05.hip",
                    "vresef432_06.hip",
                    "vresef432_07.hip",
                    "vresef432_08.hip",
                    "vresef432_09.hip",
                    "vresef432_10.hip",
                    "vresef432_11.hip",
                    "vresef432_12.hip",
                    "vresef432_13.hip",
                    "vresef432_14.hip",
                    "vresef432_15.hip",
                    "vresef432_16.hip",
                ),

                PALETTE_FILE: "es{}_04.hpl",
            },
        },
    },
}
