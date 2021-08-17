# Defined solely by alphabetical order.
# Used as an "internal ID" of sorts.
AMANE = 0
ARAKUNE = 1
AZRAEL = 2
BANG = 3
BULLET = 4
CARL = 5
CELICA = 6
ES = 7
HAKUMEN = 8
HAZAMA = 9
HIBIKI = 10
IRON_TAGER = 11
IZANAMI = 12
IZAYOI = 13
JIN = 14
JUBEI = 15
KAGURA = 16
KOKONOE = 17
LITCHI = 18
LAMBDA = 19
MAKOTO = 20
MAI = 21
MU = 22
NAOTO = 23
NINE = 24
NOEL = 25
NU = 26
PLATINUM = 27
RACHEL = 28
RAGNA = 29
RELIUS = 30
SUSANOO = 31
TAOKAKA = 32
TSUBAKI = 33
TERUMI = 34
VALKENHAYNE = 35

# Reference for character file prefixes: https://steamcommunity.com/sharedfiles/filedetails/?id=915991216
CHARACTER_INFO = {

    AMANE: ("Amane Nishiki", "am"),
    ARAKUNE: ("Arakune", "ar"),
    AZRAEL: ("Azrael", "az"),
    BANG: ("Bang Shishigami", "bn"),
    BULLET: ("Bullet", "bl"),
    CARL: ("Carl Clover", "ca"),
    CELICA: ("Celica A. Mercury", "ce"),
    ES: ("Es", "es"),
    HAKUMEN: ("Hakumen", "ha"),
    HAZAMA: ("Hazama", "hz"),
    HIBIKI: ("Hibiki Kohaku", "hb"),
    IRON_TAGER: ("Iron Tager", "tg"),
    IZANAMI: ("Izanami", "mi"),  # Mikado == Imperator
    IZAYOI: ("Izayoi", "iz"),
    JIN: ("Jin Kisaragi", "jn"),
    JUBEI: ("Jubei", "jb"),
    KAGURA: ("Kagura Mutsuki", "kg"),
    KOKONOE: ("Kokonoe", "kk"),
    LITCHI: ("Litchi Faye Ling", "lc"),
    LAMBDA: ("Lambda-11", "rm"),  # Ramuda
    MAKOTO: ("Makoto Nanaya", "mk"),
    MAI: ("Mai Natsume", "ma"),
    MU: ("Mu-12", "mu"),
    NAOTO: ("Naoto Kurogane", "nt"),
    NINE: ("Nine the Phantom", "ph"),
    NOEL: ("Noel Vermillion", "no"),
    NU: ("Nu-13", "ny"),  # Nyu
    PLATINUM: ("Platinum the Trinity", "pt"),
    RACHEL: ("Rachel Alucard", "rc"),
    RAGNA: ("Ragna the Bloodedge", "rg"),
    RELIUS: ("Relius Clover", "rl"),
    SUSANOO: ("Susano'o", "su"),
    TAOKAKA: ("Taokaka", "tk"),
    TSUBAKI: ("Tsubaki Yayoi", "tb"),
    TERUMI: ("Yuuki Terumi", "tm"),
    VALKENHAYNE: ("Valkenhayne R. Hellsing", "vh"),
}

VALID_CHARACTERS = tuple([_character for _, _character in CHARACTER_INFO.values()])

DEFAULT_PALETTE_FMT = "{}{{}}_00.hpl"

CHARACTER_STATES = 3

STATE_DEFINITION = 5
STATE_INITIAL = 6
STATE_CHANGE = 7
FILE_OVERRIDE = 8

SWAP_COLORS = 0
SWAP_PALETTES = 1

CHARACTER_INFO_EXT = {

    IZANAMI: {

        CHARACTER_STATES: {

            # This will result in a Inactive being the first displayed choice.
            STATE_DEFINITION: ("Time Stop", ("Inactive", "Active")),
            STATE_INITIAL: "Inactive",
            STATE_CHANGE: {

                SWAP_PALETTES: (

                    ("mi{}_00.hpl", "mi{}_02.hpl"),
                ),
            },
        },
    },
    IZAYOI: {

        CHARACTER_STATES: {

            # This will result in a Inactive being the first displayed choice.
            STATE_DEFINITION: ("Gain Art", ("Inactive", "Active")),
            STATE_INITIAL: "Inactive",
            STATE_CHANGE: {

                SWAP_COLORS: (

                    ((10, 11), (13, 11)),
                    ((11, 11), (14, 11)),
                    ((12, 11), (15, 11)),
                ),
                SWAP_PALETTES: (

                    ("iz{}_04.hpl", "iz{}_05.hpl"),
                ),
            },
        },
    },
    LAMBDA: {

        FILE_OVERRIDE: "ny",  # Lambda-11 uses the same character abbreviation as Nu-13 for sprite and palette files.
    }
}
