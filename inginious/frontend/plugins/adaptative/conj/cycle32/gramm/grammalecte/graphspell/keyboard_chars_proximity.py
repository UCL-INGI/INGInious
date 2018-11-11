# Keyboard chars proximity


def getKeyboardMap (sKeyboard):
    return _dKeyboardMap.get(sKeyboard.lower(), {})


def getKeyboardList ():
    return _dKeyboardMap.keys()


_dKeyboardMap = {
    # keyboards by alphabetical order
    # bépo, colemak and dvorak users are assumed to do less typing errors.
    "azerty": {
        # fr
        # line 1
        "é": "az",
        "è": "yu",
        "ç": "àio",
        "à": "op",
        # line 2
        "a": "zéq",
        "z": "aesq",
        "e": "zrds",
        "r": "etfd",
        "t": "rygf",
        "y": "tuhg",
        "u": "yijh",
        "i": "uokj",
        "o": "iplk",
        "p": "oml",
        # line 3
        "q": "sawz",
        "s": "qdzwxe",
        "d": "sfexcr",
        "f": "dgrcvt",
        "g": "fhtvby",
        "h": "gjybnu",
        "j": "hkuni",
        "k": "jlio",
        "l": "kmop",
        "m": "lùp",
        "ù": "m",
        # line 4
        "w": "xqs",
        "x": "wcsd",
        "c": "xvdf",
        "v": "cbfg",
        "b": "vngh",
        "n": "bhj",
    },
    "bépo": {
        # fr
        # line 2
        "b": "éa",
        "é": "bpu",
        "p": "éoi",
        "o": "pèe",
        "è": "o",
        "v": "dt",
        "d": "vls",
        "l": "djr",
        "j": "lzn",
        "z": "jmw",
        # line 3
        "a": "ubà",
        "u": "aiéy",
        "i": "uepx",
        "e": "io",
        "c": "t",
        "t": "csvq",
        "s": "trdg",
        "r": "snlh",
        "n": "rmjf",
        "m": "nzç",
        # line 4
        "à": "yêa",
        "y": "àxu",
        "x": "ywi",
        "w": "z",
        "k": "c",
        "q": "gt",
        "g": "qhs",
        "h": "gfr",
        "f": "hçn",
        "ç": "fm",
    },
    "colemak": {
        # en, us, intl
        # line 2
        "q": "wa",
        "w": "qfr",
        "f": "wps",
        "p": "fgt",
        "g": "pjd",
        "j": "glh",
        "l": "jun",
        "u": "lye",
        "y": "ui",
        # line 3
        "a": "rqz",
        "r": "aswx",
        "s": "rtfc",
        "t": "sdpv",
        "d": "thgb",
        "h": "dnjk",
        "n": "helm",
        "e": "niu",
        "i": "eoy",
        "o": "i",
        # line 4
        "z": "xa",
        "x": "zcr",
        "c": "xvs",
        "v": "cbt",
        "b": "vkd",
        "k": "bmh",
        "m": "kn",
    },
    "dvorak": {
        # en, us, intl
        # line 2
        "p": "yu",
        "y": "pfi",
        "f": "ygd",
        "g": "fch",
        "c": "grt",
        "r": "cln",
        "l": "rs",
        # line 3
        "a": "o",
        "o": "aeq",
        "e": "ouj",
        "u": "eipk",
        "i": "udyx",
        "d": "ihfb",
        "h": "dtgm",
        "t": "hncw",
        "n": "tsrv",
        "s": "nlz",
        # line 4
        "q": "jo",
        "j": "qke",
        "k": "jxu",
        "x": "kbi",
        "b": "xmd",
        "m": "bwh",
        "w": "mvt",
        "v": "wzn",
        "z": "vs",
    },
    "qwerty": {
        # en, us, intl
        # line 2
        "q": "wa",
        "w": "qeas",
        "e": "wrds",
        "r": "etfd",
        "t": "rygf",
        "y": "tuhg",
        "u": "yijh",
        "i": "uokj",
        "o": "iplk",
        "p": "ol",
        # line 3
        "a": "sqzw",
        "s": "adwzxe",
        "d": "sfexcr",
        "f": "dgrcvt",
        "g": "fhtvby",
        "h": "gjybnu",
        "j": "hkunmi",
        "k": "jlimo",
        "l": "kop",
        # line 4
        "z": "xas",
        "x": "zcsd",
        "c": "xvdf",
        "v": "cbfg",
        "b": "vngh",
        "n": "bmhj",
        "m": "njk",
    },
    "qwertz": {
        # ge, au
        # line 2
        "q": "wa",
        "w": "qeas",
        "e": "wrds",
        "r": "etfd",
        "t": "rzgf",
        "z": "tuhg",
        "u": "zijh",
        "i": "uokj",
        "o": "iplk",
        "p": "oüöl",
        "ü": "päö",
        # line 3
        "a": "sqyw",
        "s": "adwyxe",
        "d": "sfexcr",
        "f": "dgrcvt",
        "g": "fhtvbz",
        "h": "gjzbnu",
        "j": "hkunmi",
        "k": "jlimo",
        "l": "köop",
        "ö": "läpü",
        "ä": "öü",
        # line 4
        "y": "xas",
        "x": "ycsd",
        "c": "xvdf",
        "v": "cbfg",
        "b": "vngh",
        "n": "bmhj",
        "m": "njk",
    }
}
