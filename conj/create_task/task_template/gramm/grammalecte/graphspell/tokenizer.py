# Very simple tokenizer

import re

_PATTERNS = {
    "default":
        (
            r'(?P<FOLDERUNIX>/(?:bin|boot|dev|etc|home|lib|mnt|opt|root|sbin|tmp|usr|var|Bureau|Documents|Images|Musique|Public|Téléchargements|Vidéos)(?:/[\w.()-]+)*)',
            r'(?P<FOLDERWIN>[a-zA-Z]:\\(?:Program Files(?: [(]x86[)]|)|[\w.()]+)(?:\\[\w.()-]+)*)',
            r'(?P<PUNC>[.,?!:;…«»“”"()/·]+)',
            r'(?P<ACRONYM>[A-Z][.][A-Z][.](?:[A-Z][.])*)',
            r'(?P<LINK>(?:https?://|www[.]|\w+[@.]\w\w+[@.])\w[\w./?&!%=+*"\'@$#-]+)',
            r'(?P<HASHTAG>[#@][\w-]+)',
            r'(?P<HTML><\w+.*?>|</\w+ *>)',
            r'(?P<PSEUDOHTML>\[/?\w+\])',
            r'(?P<HOUR>\d\d?h\d\d\b)',
            r'(?P<NUM>-?\d+(?:[.,]\d+))',
            r"(?P<WORD>\w+(?:[’'`-]\w+)*)"
        ),
    "fr":
        (
            r'(?P<FOLDERUNIX>/(?:bin|boot|dev|etc|home|lib|mnt|opt|root|sbin|tmp|usr|var|Bureau|Documents|Images|Musique|Public|Téléchargements|Vidéos)(?:/[\w.()-]+)*)',
            r'(?P<FOLDERWIN>[a-zA-Z]:\\(?:Program Files(?: [(]x86[)]|)|[\w.()]+)(?:\\[\w.()-]+)*)',
            r'(?P<PUNC>[.,?!:;…«»“”"()/·]+)',
            r'(?P<ACRONYM>[A-Z][.][A-Z][.](?:[A-Z][.])*)',
            r'(?P<LINK>(?:https?://|www[.]|\w+[@.]\w\w+[@.])\w[\w./?&!%=+*"\'@$#-]+)',
            r'(?P<HASHTAG>[#@][\w-]+)',
            r'(?P<HTML><\w+.*?>|</\w+ *>)',
            r'(?P<PSEUDOHTML>\[/?\w+\])',
            r"(?P<ELPFX>(?:l|d|n|m|t|s|j|c|ç|lorsqu|puisqu|jusqu|quoiqu|qu)['’`])",
            r'(?P<ORDINAL>\d+(?:er|nd|e|de|ième|ème|eme)\b)',
            r'(?P<HOUR>\d\d?h\d\d\b)',
            r'(?P<NUM>-?\d+(?:[.,]\d+|))',
            r"(?P<WORD>\w+(?:[’'`-]\w+)*)"
        )
}


class Tokenizer:

    def __init__ (self, sLang):
        self.sLang = sLang
        if sLang not in _PATTERNS:
            self.sLang = "default"
        self.zToken = re.compile( "(?i)" + '|'.join(sRegex for sRegex in _PATTERNS[sLang]) )

    def genTokens (self, sText):
        for m in self.zToken.finditer(sText):
            yield { "sType": m.lastgroup, "sValue": m.group(), "nStart": m.start(), "nEnd": m.end() }
