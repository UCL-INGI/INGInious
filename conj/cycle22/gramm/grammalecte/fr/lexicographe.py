# Grammalecte - Lexicographe
# License: MPL 2


import re
import traceback


_dTAGS = {  
    ':G': "",
    ':N': " nom,",
    ':A': " adjectif,",
    ':M1': " prénom,",
    ':M2': " patronyme,",
    ':MP': " nom propre,",
    ':W': " adverbe,",
    ':X': " adverbe de négation,",
    ':U': " adverbe interrogatif,",
    ':J': " interjection,",
    ':B': " nombre,",
    ':T': " titre,",

    ':R': " préposition,",
    ':Rv': " préposition verbale,",
    ':D': " déterminant,",
    ':Dd': " déterminant démonstratif,",
    ':De': " déterminant exclamatif,",
    ':Dp': " déterminant possessif,",
    ':Di': " déterminant indéfini,",
    ':Dn': " déterminant négatif,",
    ':Od': " pronom démonstratif,",
    ':Oi': " pronom indéfini,",
    ':On': " pronom indéfini négatif,",
    ':Ot': " pronom interrogatif,",
    ':Or': " pronom relatif,",
    ':Ow': " pronom adverbial,",
    ':Os': " pronom personnel sujet,",
    ':Oo': " pronom personnel objet,",
    ':C': " conjonction,",
    ':Ĉ': " conjonction (él.),",
    ':Cc': " conjonction de coordination,",
    ':Cs': " conjonction de subordination,",
    ':Ĉs': " conjonction de subordination (él.),",
    
    ':Ŵ': " locution adverbiale (él.),",
    ':Ñ': " locution nominale (él.),",
    ':Â': " locution adjectivale (él.),",
    ':Ṽ': " locution verbale (él.),",
    ':Ŕ': " locution prépositive (él.),",
    ':Ĵ': " locution interjective (él.),",

    ':Zp': " préfixe,",
    ':Zs': " suffixe,",

    ':V1': " verbe (1ᵉʳ gr.),",
    ':V2': " verbe (2ᵉ gr.),",
    ':V3': " verbe (3ᵉ gr.),",
    ':V0e': " verbe,",
    ':V0a': " verbe,",

    ':O1': " 1ʳᵉ pers.,",
    ':O2': " 2ᵉ pers.,",
    ':O3': " 3ᵉ pers.,",
    
    ':e': " épicène",
    ':m': " masculin",
    ':f': " féminin",
    ':s': " singulier",
    ':p': " pluriel",
    ':i': " invariable",

    ':Y': " infinitif,",
    ':P': " participe présent,",
    ':Q': " participe passé,",

    ':Ip': " présent,",
    ':Iq': " imparfait,",
    ':Is': " passé simple,",
    ':If': " futur,",
    ':K': " conditionnel présent,",
    ':Sp': " subjonctif présent,",
    ':Sq': " subjonctif imparfait,",
    ':E': " impératif,",

    ':1s': " 1ʳᵉ p. sg.,",
    ':1ŝ': " présent interr. 1ʳᵉ p. sg.,",
    ':1ś': " présent interr. 1ʳᵉ p. sg.,",
    ':2s': " 2ᵉ p. sg.,",
    ':3s': " 3ᵉ p. sg.,",
    ':1p': " 1ʳᵉ p. pl.,",
    ':2p': " 2ᵉ p. pl.,",
    ':3p': " 3ᵉ p. pl.,",
    ':3p!': " 3ᵉ p. pl.,",

    ';S': " : symbole (unité de mesure)",

    '/*': "",
    '/C': " {classique}",
    '/M': "",
    '/R': " {réforme}",
    '/A': "",
    '/X': ""
}

_dPFX = {
    'd': "(de), déterminant épicène invariable",
    'l': "(le/la), déterminant masculin/féminin singulier",
    'j': "(je), pronom personnel sujet, 1ʳᵉ pers., épicène singulier",
    'm': "(me), pronom personnel objet, 1ʳᵉ pers., épicène singulier",
    't': "(te), pronom personnel objet, 2ᵉ pers., épicène singulier",
    's': "(se), pronom personnel objet, 3ᵉ pers., épicène singulier/pluriel",
    'n': "(ne), adverbe de négation",
    'c': "(ce), pronom démonstratif, masculin singulier/pluriel",
    'ç': "(ça), pronom démonstratif, masculin singulier",
    'qu': "(que), conjonction de subordination",
    'lorsqu': "(lorsque), conjonction de subordination",
    'quoiqu': "(quoique), conjonction de subordination",
    'jusqu': "(jusque), préposition",
}

_dAD = {
    'je': " pronom personnel sujet, 1ʳᵉ pers. sing.",
    'tu': " pronom personnel sujet, 2ᵉ pers. sing.",
    'il': " pronom personnel sujet, 3ᵉ pers. masc. sing.",
    'on': " pronom personnel sujet, 3ᵉ pers. sing. ou plur.",
    'elle': " pronom personnel sujet, 3ᵉ pers. fém. sing.",
    'nous': " pronom personnel sujet/objet, 1ʳᵉ pers. plur.",
    'vous': " pronom personnel sujet/objet, 2ᵉ pers. plur.",
    'ils': " pronom personnel sujet, 3ᵉ pers. masc. plur.",
    'elles': " pronom personnel sujet, 3ᵉ pers. masc. plur.",
    
    "là": " particule démonstrative",
    "ci": " particule démonstrative",
    
    'le': " COD, masc. sing.",
    'la': " COD, fém. sing.",
    'les': " COD, plur.",
        
    'moi': " COI (à moi), sing.",
    'toi': " COI (à toi), sing.",
    'lui': " COI (à lui ou à elle), sing.",
    'nous2': " COI (à nous), plur.",
    'vous2': " COI (à vous), plur.",
    'leur': " COI (à eux ou à elles), plur.",

    'y': " pronom adverbial",
    "m'y": " (me) pronom personnel objet + (y) pronom adverbial",
    "t'y": " (te) pronom personnel objet + (y) pronom adverbial",
    "s'y": " (se) pronom personnel objet + (y) pronom adverbial",

    'en': " pronom adverbial",
    "m'en": " (me) pronom personnel objet + (en) pronom adverbial",
    "t'en": " (te) pronom personnel objet + (en) pronom adverbial",
    "s'en": " (se) pronom personnel objet + (en) pronom adverbial",
}


class Lexicographe:

    def __init__ (self, oSpellChecker):
        self.oSpellChecker = oSpellChecker
        self._zElidedPrefix = re.compile("(?i)^([dljmtsncç]|quoiqu|lorsqu|jusqu|puisqu|qu)['’](.+)")
        self._zCompoundWord = re.compile("(?i)(\\w+)-((?:les?|la)-(?:moi|toi|lui|[nv]ous|leur)|t-(?:il|elle|on)|y|en|[mts][’'](?:y|en)|les?|l[aà]|[mt]oi|leur|lui|je|tu|ils?|elles?|on|[nv]ous)$")
        self._zTag = re.compile("[:;/][\\w*][^:;/]*")

    def analyzeWord (self, sWord):
        try:
            if not sWord:
                return (None, None)
            if sWord.count("-") > 4:
                return (["élément complexe indéterminé"], None)
            if sWord.isdigit():
                return (["nombre"], None)

            aMorph = []
            # préfixes élidés
            m = self._zElidedPrefix.match(sWord)
            if m:
                sWord = m.group(2)
                aMorph.append( "{}’ : {}".format(m.group(1), _dPFX.get(m.group(1).lower(), "[?]")) )
            # mots composés
            m2 = self._zCompoundWord.match(sWord)
            if m2:
                sWord = m2.group(1)
            # Morphologies
            lMorph = self.oSpellChecker.getMorph(sWord)
            if len(lMorph) > 1:
                # sublist
                aMorph.append( (sWord, [ self.formatTags(s)  for s in lMorph  if ":" in s ]) )
            elif len(lMorph) == 1:
                aMorph.append( "{} : {}".format(sWord, self.formatTags(lMorph[0])) )
            else:
                aMorph.append( "{} :  inconnu du dictionnaire".format(sWord) )
            # suffixe d’un mot composé
            if m2:
                aMorph.append( "-{} : {}".format(m2.group(2), self._formatSuffix(m2.group(2).lower())) )
            # Verbes
            aVerb = set([ s[1:s.find(" ")]  for s in lMorph  if ":V" in s ])
            return (aMorph, aVerb)
        except:
            traceback.print_exc()
            return (["#erreur"], None)

    def formatTags (self, sTags):
        sRes = ""
        sTags = re.sub("(?<=V[1-3])[itpqnmr_eaxz]+", "", sTags)
        sTags = re.sub("(?<=V0[ea])[itpqnmr_eaxz]+", "", sTags)
        for m in self._zTag.finditer(sTags):
            sRes += _dTAGS.get(m.group(0), " [{}]".format(m.group(0)))
        if sRes.startswith(" verbe") and not sRes.endswith("infinitif"):
            sRes += " [{}]".format(sTags[1:sTags.find(" ")])
        return sRes.rstrip(",")

    def _formatSuffix (self, s):
        if s.startswith("t-"):
            return "“t” euphonique +" + _dAD.get(s[2:], "[?]")
        if not "-" in s:
            return _dAD.get(s.replace("’", "'"), "[?]")
        if s.endswith("ous"):
            s += '2'
        nPos = s.find("-")
        return "%s +%s" % (_dAD.get(s[:nPos], "[?]"), _dAD.get(s[nPos+1:], "[?]"))
