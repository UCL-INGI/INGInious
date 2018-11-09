# Grammalecte
# Grammar checker engine

import re
import sys
import os
import traceback
#import unicodedata
from itertools import chain

from ..graphspell.spellchecker import SpellChecker
from ..graphspell.echo import echo
from . import gc_options


__all__ = [ "lang", "locales", "pkg", "name", "version", "author", \
            "load", "parse", "getSpellChecker", \
            "setOption", "setOptions", "getOptions", "getDefaultOptions", "getOptionsLabels", "resetOptions", "displayOptions", \
            "ignoreRule", "resetIgnoreRules", "reactivateRule", "listRules", "displayRules" ]

__version__ = "0.6.2"


lang = "fr"
locales = {'fr-FR': ['fr', 'FR', ''], 'fr-BE': ['fr', 'BE', ''], 'fr-CA': ['fr', 'CA', ''], 'fr-CH': ['fr', 'CH', ''], 'fr-LU': ['fr', 'LU', ''], 'fr-MC': ['fr', 'MC', ''], 'fr-BF': ['fr', 'BF', ''], 'fr-CI': ['fr', 'CI', ''], 'fr-SN': ['fr', 'SN', ''], 'fr-ML': ['fr', 'ML', ''], 'fr-NE': ['fr', 'NE', ''], 'fr-TG': ['fr', 'TG', ''], 'fr-BJ': ['fr', 'BJ', '']}
pkg = "grammalecte"
name = "Grammalecte"
version = "0.6.2"
author = "Olivier R."

_rules = None                               # module gc_rules

# data
_sAppContext = ""                           # what software is running
_dOptions = None
_aIgnoredRules = set()
_oSpellChecker = None
_dAnalyses = {}                             # cache for data from dictionary



#### Parsing

def parse (sText, sCountry="FR", bDebug=False, dOptions=None, bContext=False):
    "analyses the paragraph sText and returns list of errors"
    #sText = unicodedata.normalize("NFC", sText)
    aErrors = None
    sAlt = sText
    dDA = {}        # Disambiguisator. Key = position; value = list of morphologies
    dPriority = {}  # Key = position; value = priority
    dOpt = _dOptions  if not dOptions  else dOptions

    # parse paragraph
    try:
        sNew, aErrors = _proofread(sText, sAlt, 0, True, dDA, dPriority, sCountry, dOpt, bDebug, bContext)
        if sNew:
            sText = sNew
    except:
        raise

    # cleanup
    if " " in sText:
        sText = sText.replace(" ", ' ') # nbsp
    if " " in sText:
        sText = sText.replace(" ", ' ') # nnbsp
    if "'" in sText:
        sText = sText.replace("'", "’")
    if "‑" in sText:
        sText = sText.replace("‑", "-") # nobreakdash

    # parse sentences
    for iStart, iEnd in _getSentenceBoundaries(sText):
        if 4 < (iEnd - iStart) < 2000:
            dDA.clear()
            try:
                _, errs = _proofread(sText[iStart:iEnd], sAlt[iStart:iEnd], iStart, False, dDA, dPriority, sCountry, dOpt, bDebug, bContext)
                aErrors.update(errs)
            except:
                raise
    return aErrors.values() # this is a view (iterable)


def _getSentenceBoundaries (sText):
    iStart = _zBeginOfParagraph.match(sText).end()
    for m in _zEndOfSentence.finditer(sText):
        yield (iStart, m.end())
        iStart = m.end()


def _proofread (s, sx, nOffset, bParagraph, dDA, dPriority, sCountry, dOptions, bDebug, bContext):
    dErrs = {}
    bChange = False
    bIdRule = option('idrule')

    for sOption, lRuleGroup in _getRules(bParagraph):
        if not sOption or dOptions.get(sOption, False):
            for zRegex, bUppercase, sLineId, sRuleId, nPriority, lActions in lRuleGroup:
                if sRuleId not in _aIgnoredRules:
                    for m in zRegex.finditer(s):
                        bCondMemo = None
                        for sFuncCond, cActionType, sWhat, *eAct in lActions:
                            # action in lActions: [ condition, action type, replacement/suggestion/action[, iGroup[, message, URL]] ]
                            try:
                                bCondMemo = not sFuncCond or globals()[sFuncCond](s, sx, m, dDA, sCountry, bCondMemo)
                                if bCondMemo:
                                    if cActionType == "-":
                                        # grammar error
                                        nErrorStart = nOffset + m.start(eAct[0])
                                        if nErrorStart not in dErrs or nPriority > dPriority[nErrorStart]:
                                            dErrs[nErrorStart] = _createError(s, sx, sWhat, nOffset, m, eAct[0], sLineId, sRuleId, bUppercase, eAct[1], eAct[2], bIdRule, sOption, bContext)
                                            dPriority[nErrorStart] = nPriority
                                    elif cActionType == "~":
                                        # text processor
                                        s = _rewrite(s, sWhat, eAct[0], m, bUppercase)
                                        bChange = True
                                        if bDebug:
                                            echo("~ " + s + "  -- " + m.group(eAct[0]) + "  # " + sLineId)
                                    elif cActionType == "=":
                                        # disambiguation
                                        globals()[sWhat](s, m, dDA)
                                        if bDebug:
                                            echo("= " + m.group(0) + "  # " + sLineId + "\nDA: " + str(dDA))
                                    elif cActionType == ">":
                                        # we do nothing, this test is just a condition to apply all following actions
                                        pass
                                    else:
                                        echo("# error: unknown action at " + sLineId)
                                elif cActionType == ">":
                                    break
                            except Exception as e:
                                raise Exception(str(e), "# " + sLineId + " # " + sRuleId)
    if bChange:
        return (s, dErrs)
    return (False, dErrs)


def _createWriterError (s, sx, sRepl, nOffset, m, iGroup, sLineId, sRuleId, bUppercase, sMsg, sURL, bIdRule, sOption, bContext):
    "error for Writer (LO/OO)"
    xErr = SingleProofreadingError()
    #xErr = uno.createUnoStruct( "com.sun.star.linguistic2.SingleProofreadingError" )
    xErr.nErrorStart = nOffset + m.start(iGroup)
    xErr.nErrorLength = m.end(iGroup) - m.start(iGroup)
    xErr.nErrorType = PROOFREADING
    xErr.aRuleIdentifier = sRuleId
    # suggestions
    if sRepl[0:1] == "=":
        sugg = globals()[sRepl[1:]](s, m)
        if sugg:
            if bUppercase and m.group(iGroup)[0:1].isupper():
                xErr.aSuggestions = tuple(map(str.capitalize, sugg.split("|")))
            else:
                xErr.aSuggestions = tuple(sugg.split("|"))
        else:
            xErr.aSuggestions = ()
    elif sRepl == "_":
        xErr.aSuggestions = ()
    else:
        if bUppercase and m.group(iGroup)[0:1].isupper():
            xErr.aSuggestions = tuple(map(str.capitalize, m.expand(sRepl).split("|")))
        else:
            xErr.aSuggestions = tuple(m.expand(sRepl).split("|"))
    # Message
    if sMsg[0:1] == "=":
        sMessage = globals()[sMsg[1:]](s, m)
    else:
        sMessage = m.expand(sMsg)
    xErr.aShortComment = sMessage   # sMessage.split("|")[0]     # in context menu
    xErr.aFullComment = sMessage   # sMessage.split("|")[-1]    # in dialog
    if bIdRule:
        xErr.aShortComment += "  # " + sLineId + " # " + sRuleId
    # URL
    if sURL:
        p = PropertyValue()
        p.Name = "FullCommentURL"
        p.Value = sURL
        xErr.aProperties = (p,)
    else:
        xErr.aProperties = ()
    return xErr


def _createDictError (s, sx, sRepl, nOffset, m, iGroup, sLineId, sRuleId, bUppercase, sMsg, sURL, bIdRule, sOption, bContext):
    "error as a dictionary"
    dErr = {}
    dErr["nStart"] = nOffset + m.start(iGroup)
    dErr["nEnd"] = nOffset + m.end(iGroup)
    dErr["sLineId"] = sLineId
    dErr["sRuleId"] = sRuleId
    dErr["sType"] = sOption  if sOption  else "notype"
    # suggestions
    if sRepl[0:1] == "=":
        sugg = globals()[sRepl[1:]](s, m)
        if sugg:
            if bUppercase and m.group(iGroup)[0:1].isupper():
                dErr["aSuggestions"] = list(map(str.capitalize, sugg.split("|")))
            else:
                dErr["aSuggestions"] = sugg.split("|")
        else:
            dErr["aSuggestions"] = ()
    elif sRepl == "_":
        dErr["aSuggestions"] = ()
    else:
        if bUppercase and m.group(iGroup)[0:1].isupper():
            dErr["aSuggestions"] = list(map(str.capitalize, m.expand(sRepl).split("|")))
        else:
            dErr["aSuggestions"] = m.expand(sRepl).split("|")
    # Message
    if sMsg[0:1] == "=":
        sMessage = globals()[sMsg[1:]](s, m)
    else:
        sMessage = m.expand(sMsg)
    dErr["sMessage"] = sMessage
    if bIdRule:
        dErr["sMessage"] += "  # " + sLineId + " # " + sRuleId
    # URL
    dErr["URL"] = sURL  if sURL  else ""
    # Context
    if bContext:
        dErr['sUnderlined'] = sx[m.start(iGroup):m.end(iGroup)]
        dErr['sBefore'] = sx[max(0,m.start(iGroup)-80):m.start(iGroup)]
        dErr['sAfter'] = sx[m.end(iGroup):m.end(iGroup)+80]
    return dErr


def _rewrite (s, sRepl, iGroup, m, bUppercase):
    "text processor: write sRepl in s at iGroup position"
    nLen = m.end(iGroup) - m.start(iGroup)
    if sRepl == "*":
        sNew = " " * nLen
    elif sRepl == ">" or sRepl == "_" or sRepl == "~":
        sNew = sRepl + " " * (nLen-1)
    elif sRepl == "@":
        sNew = "@" * nLen
    elif sRepl[0:1] == "=":
        sNew = globals()[sRepl[1:]](s, m)
        sNew = sNew + " " * (nLen-len(sNew))
        if bUppercase and m.group(iGroup)[0:1].isupper():
            sNew = sNew.capitalize()
    else:
        sNew = m.expand(sRepl)
        sNew = sNew + " " * (nLen-len(sNew))
    return s[0:m.start(iGroup)] + sNew + s[m.end(iGroup):]


def ignoreRule (sRuleId):
    _aIgnoredRules.add(sRuleId)


def resetIgnoreRules ():
    _aIgnoredRules.clear()


def reactivateRule (sRuleId):
    _aIgnoredRules.discard(sRuleId)


def listRules (sFilter=None):
    "generator: returns typle (sOption, sLineId, sRuleId)"
    if sFilter:
        try:
            zFilter = re.compile(sFilter)
        except:
            echo("# Error. List rules: wrong regex.")
            sFilter = None
    for sOption, lRuleGroup in chain(_getRules(True), _getRules(False)):
        for _, _, sLineId, sRuleId, _, _ in lRuleGroup:
            if not sFilter or zFilter.search(sRuleId):
                yield (sOption, sLineId, sRuleId)


def displayRules (sFilter=None):
    echo("List of rules. Filter: << " + str(sFilter) + " >>")
    for sOption, sLineId, sRuleId in listRules(sFilter):
        echo("{:<10} {:<10} {}".format(sOption, sLineId, sRuleId))


#### init

try:
    # LibreOffice / OpenOffice
    from com.sun.star.linguistic2 import SingleProofreadingError
    from com.sun.star.text.TextMarkupType import PROOFREADING
    from com.sun.star.beans import PropertyValue
    #import lightproof_handler_grammalecte as opt
    _createError = _createWriterError
except ImportError:
    _createError = _createDictError


def load (sContext="Python"):
    global _oSpellChecker
    global _sAppContext
    global _dOptions
    try:
        _oSpellChecker = SpellChecker("fr", "fr.bdic", "", "")
        _sAppContext = sContext
        _dOptions = dict(gc_options.getOptions(sContext))   # duplication necessary, to be able to reset to default
    except:
        traceback.print_exc()


def setOption (sOpt, bVal):
    if sOpt in _dOptions:
        _dOptions[sOpt] = bVal


def setOptions (dOpt):
    for sKey, bVal in dOpt.items():
        if sKey in _dOptions:
            _dOptions[sKey] = bVal


def getOptions ():
    return _dOptions


def getDefaultOptions ():
    return dict(gc_options.getOptions(_sAppContext))


def getOptionsLabels (sLang):
    return gc_options.getUI(sLang)


def displayOptions (sLang):
    echo("List of options")
    echo("\n".join( [ k+":\t"+str(v)+"\t"+gc_options.getUI(sLang).get(k, ("?", ""))[0]  for k, v  in sorted(_dOptions.items()) ] ))
    echo("")


def resetOptions ():
    global _dOptions
    _dOptions = dict(gc_options.getOptions(_sAppContext))


def getSpellChecker ():
    return _oSpellChecker


def _getRules (bParagraph):
    try:
        if not bParagraph:
            return _rules.lSentenceRules
        return _rules.lParagraphRules
    except:
        _loadRules()
    if not bParagraph:
        return _rules.lSentenceRules
    return _rules.lParagraphRules


def _loadRules ():
    from . import gc_rules
    global _rules
    _rules = gc_rules
    # compile rules regex
    for lRuleGroup in chain(_rules.lParagraphRules, _rules.lSentenceRules):
        for rule in lRuleGroup[1]:
            try:
                rule[0] = re.compile(rule[0])
            except:
                echo("Bad regular expression in # " + str(rule[2]))
                rule[0] = "(?i)<Grammalecte>"


def _getPath ():
    return os.path.join(os.path.dirname(sys.modules[__name__].__file__), __name__ + ".py")



#### common functions

# common regexes
_zEndOfSentence = re.compile('([.?!:;…][ .?!… »”")]*|.$)')
_zBeginOfParagraph = re.compile("^\W*")
_zEndOfParagraph = re.compile("\W*$")
_zNextWord = re.compile(" +(\w[\w-]*)")
_zPrevWord = re.compile("(\w[\w-]*) +$")


def option (sOpt):
    "return True if option sOpt is active"
    return _dOptions.get(sOpt, False)


def displayInfo (dDA, tWord):
    "for debugging: retrieve info of word"
    if not tWord:
        echo("> nothing to find")
        return True
    if tWord[1] not in _dAnalyses and not _storeMorphFromFSA(tWord[1]):
        echo("> not in FSA")
        return True
    if tWord[0] in dDA:
        echo("DA: " + str(dDA[tWord[0]]))
    echo("FSA: " + str(_dAnalyses[tWord[1]]))
    return True


def _storeMorphFromFSA (sWord):
    "retrieves morphologies list from _oSpellChecker -> _dAnalyses"
    global _dAnalyses
    _dAnalyses[sWord] = _oSpellChecker.getMorph(sWord)
    return True  if _dAnalyses[sWord]  else False


def morph (dDA, tWord, sPattern, bStrict=True, bNoWord=False):
    "analyse a tuple (position, word), return True if sPattern in morphologies (disambiguation on)"
    if not tWord:
        return bNoWord
    if tWord[1] not in _dAnalyses and not _storeMorphFromFSA(tWord[1]):
        return False
    lMorph = dDA[tWord[0]]  if tWord[0] in dDA  else _dAnalyses[tWord[1]]
    if not lMorph:
        return False
    p = re.compile(sPattern)
    if bStrict:
        return all(p.search(s)  for s in lMorph)
    return any(p.search(s)  for s in lMorph)


def morphex (dDA, tWord, sPattern, sNegPattern, bNoWord=False):
    "analyse a tuple (position, word), returns True if not sNegPattern in word morphologies and sPattern in word morphologies (disambiguation on)"
    if not tWord:
        return bNoWord
    if tWord[1] not in _dAnalyses and not _storeMorphFromFSA(tWord[1]):
        return False
    lMorph = dDA[tWord[0]]  if tWord[0] in dDA  else _dAnalyses[tWord[1]]
    # check negative condition
    np = re.compile(sNegPattern)
    if any(np.search(s)  for s in lMorph):
        return False
    # search sPattern
    p = re.compile(sPattern)
    return any(p.search(s)  for s in lMorph)


def analyse (sWord, sPattern, bStrict=True):
    "analyse a word, return True if sPattern in morphologies (disambiguation off)"
    if sWord not in _dAnalyses and not _storeMorphFromFSA(sWord):
        return False
    if not _dAnalyses[sWord]:
        return False
    p = re.compile(sPattern)
    if bStrict:
        return all(p.search(s)  for s in _dAnalyses[sWord])
    return any(p.search(s)  for s in _dAnalyses[sWord])


def analysex (sWord, sPattern, sNegPattern):
    "analyse a word, returns True if not sNegPattern in word morphologies and sPattern in word morphologies (disambiguation off)"
    if sWord not in _dAnalyses and not _storeMorphFromFSA(sWord):
        return False
    # check negative condition
    np = re.compile(sNegPattern)
    if any(np.search(s)  for s in _dAnalyses[sWord]):
        return False
    # search sPattern
    p = re.compile(sPattern)
    return any(p.search(s)  for s in _dAnalyses[sWord])


def stem (sWord):
    "returns a list of sWord's stems"
    if not sWord:
        return []
    if sWord not in _dAnalyses and not _storeMorphFromFSA(sWord):
        return []
    return [ s[1:s.find(" ")]  for s in _dAnalyses[sWord] ]


## functions to get text outside pattern scope

# warning: check compile_rules.py to understand how it works

def nextword (s, iStart, n):
    "get the nth word of the input string or empty string"
    m = re.match("(?: +[\\w%-]+){" + str(n-1) + "} +([\\w%-]+)", s[iStart:])
    if not m:
        return None
    return (iStart+m.start(1), m.group(1))


def prevword (s, iEnd, n):
    "get the (-)nth word of the input string or empty string"
    m = re.search("([\\w%-]+) +(?:[\\w%-]+ +){" + str(n-1) + "}$", s[:iEnd])
    if not m:
        return None
    return (m.start(1), m.group(1))


def nextword1 (s, iStart):
    "get next word (optimization)"
    m = _zNextWord.match(s[iStart:])
    if not m:
        return None
    return (iStart+m.start(1), m.group(1))


def prevword1 (s, iEnd):
    "get previous word (optimization)"
    m = _zPrevWord.search(s[:iEnd])
    if not m:
        return None
    return (m.start(1), m.group(1))


def look (s, sPattern, sNegPattern=None):
    "seek sPattern in s (before/after/fulltext), if sNegPattern not in s"
    if sNegPattern and re.search(sNegPattern, s):
        return False
    if re.search(sPattern, s):
        return True
    return False


def look_chk1 (dDA, s, nOffset, sPattern, sPatternGroup1, sNegPatternGroup1=None):
    "returns True if s has pattern sPattern and m.group(1) has pattern sPatternGroup1"
    m = re.search(sPattern, s)
    if not m:
        return False
    try:
        sWord = m.group(1)
        nPos = m.start(1) + nOffset
    except:
        return False
    if sNegPatternGroup1:
        return morphex(dDA, (nPos, sWord), sPatternGroup1, sNegPatternGroup1)
    return morph(dDA, (nPos, sWord), sPatternGroup1, False)


#### Disambiguator

def select (dDA, nPos, sWord, sPattern, lDefault=None):
    if not sWord:
        return True
    if nPos in dDA:
        return True
    if sWord not in _dAnalyses and not _storeMorphFromFSA(sWord):
        return True
    if len(_dAnalyses[sWord]) == 1:
        return True
    lSelect = [ sMorph  for sMorph in _dAnalyses[sWord]  if re.search(sPattern, sMorph) ]
    if lSelect:
        if len(lSelect) != len(_dAnalyses[sWord]):
            dDA[nPos] = lSelect
            #echo("= "+sWord+" "+str(dDA.get(nPos, "null")))
    elif lDefault:
        dDA[nPos] = lDefault
        #echo("= "+sWord+" "+str(dDA.get(nPos, "null")))
    return True


def exclude (dDA, nPos, sWord, sPattern, lDefault=None):
    if not sWord:
        return True
    if nPos in dDA:
        return True
    if sWord not in _dAnalyses and not _storeMorphFromFSA(sWord):
        return True
    if len(_dAnalyses[sWord]) == 1:
        return True
    lSelect = [ sMorph  for sMorph in _dAnalyses[sWord]  if not re.search(sPattern, sMorph) ]
    if lSelect:
        if len(lSelect) != len(_dAnalyses[sWord]):
            dDA[nPos] = lSelect
            #echo("= "+sWord+" "+str(dDA.get(nPos, "null")))
    elif lDefault:
        dDA[nPos] = lDefault
        #echo("= "+sWord+" "+str(dDA.get(nPos, "null")))
    return True


def define (dDA, nPos, lMorph):
    dDA[nPos] = lMorph
    #echo("= "+str(nPos)+" "+str(dDA[nPos]))
    return True


#### GRAMMAR CHECKER PLUGINS



#### GRAMMAR CHECKING ENGINE PLUGIN: Parsing functions for French language

from . import cregex as cr


def rewriteSubject (s1, s2):
    # s1 is supposed to be prn/patr/npr (M[12P])
    if s2 == "lui":
        return "ils"
    if s2 == "moi":
        return "nous"
    if s2 == "toi":
        return "vous"
    if s2 == "nous":
        return "nous"
    if s2 == "vous":
        return "vous"
    if s2 == "eux":
        return "ils"
    if s2 == "elle" or s2 == "elles":
        # We don’t check if word exists in _dAnalyses, for it is assumed it has been done before
        if cr.mbNprMasNotFem(_dAnalyses.get(s1, False)):
            return "ils"
        # si épicène, indéterminable, mais OSEF, le féminin l’emporte
        return "elles"
    return s1 + " et " + s2


def apposition (sWord1, sWord2):
    "returns True if nom + nom (no agreement required)"
    # We don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    return cr.mbNomNotAdj(_dAnalyses.get(sWord2, False)) and cr.mbPpasNomNotAdj(_dAnalyses.get(sWord1, False))


def isAmbiguousNAV (sWord):
    "words which are nom|adj and verb are ambiguous (except être and avoir)"
    if sWord not in _dAnalyses and not _storeMorphFromFSA(sWord):
        return False
    if not cr.mbNomAdj(_dAnalyses[sWord]) or sWord == "est":
        return False
    if cr.mbVconj(_dAnalyses[sWord]) and not cr.mbMG(_dAnalyses[sWord]):
        return True
    return False


def isAmbiguousAndWrong (sWord1, sWord2, sReqMorphNA, sReqMorphConj):
    "use it if sWord1 won’t be a verb; word2 is assumed to be True via isAmbiguousNAV"
    # We don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    a2 = _dAnalyses.get(sWord2, None)
    if not a2:
        return False
    if cr.checkConjVerb(a2, sReqMorphConj):
        # verb word2 is ok
        return False
    a1 = _dAnalyses.get(sWord1, None)
    if not a1:
        return False
    if cr.checkAgreement(a1, a2) and (cr.mbAdj(a2) or cr.mbAdj(a1)):
        return False
    return True


def isVeryAmbiguousAndWrong (sWord1, sWord2, sReqMorphNA, sReqMorphConj, bLastHopeCond):
    "use it if sWord1 can be also a verb; word2 is assumed to be True via isAmbiguousNAV"
    # We don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    a2 = _dAnalyses.get(sWord2, None)
    if not a2:
        return False
    if cr.checkConjVerb(a2, sReqMorphConj):
        # verb word2 is ok
        return False
    a1 = _dAnalyses.get(sWord1, None)
    if not a1:
        return False
    if cr.checkAgreement(a1, a2) and (cr.mbAdj(a2) or cr.mbAdjNb(a1)):
        return False
    # now, we know there no agreement, and conjugation is also wrong
    if cr.isNomAdj(a1):
        return True
    #if cr.isNomAdjVerb(a1): # considered True
    if bLastHopeCond:
        return True
    return False


def checkAgreement (sWord1, sWord2):
    # We don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    a2 = _dAnalyses.get(sWord2, None)
    if not a2:
        return True
    a1 = _dAnalyses.get(sWord1, None)
    if not a1:
        return True
    return cr.checkAgreement(a1, a2)


_zUnitSpecial = re.compile("[µ/⁰¹²³⁴⁵⁶⁷⁸⁹Ωℓ·]")
_zUnitNumbers = re.compile("[0-9]")

def mbUnit (s):
    if _zUnitSpecial.search(s):
        return True
    if 1 < len(s) < 16 and s[0:1].islower() and (not s[1:].islower() or _zUnitNumbers.search(s)):
        return True
    return False


#### Syntagmes

_zEndOfNG1 = re.compile(" *$| +(?:, +|)(?:n(?:’|e |o(?:u?s|tre) )|l(?:’|e(?:urs?|s|) |a )|j(?:’|e )|m(?:’|es? |a |on )|t(?:’|es? |a |u )|s(?:’|es? |a )|c(?:’|e(?:t|tte|s|) )|ç(?:a |’)|ils? |vo(?:u?s|tre) )")
_zEndOfNG2 = re.compile(r" +(\w[\w-]+)")
_zEndOfNG3 = re.compile(r" *, +(\w[\w-]+)")

def isEndOfNG (dDA, s, iOffset):
    if _zEndOfNG1.match(s):
        return True
    m = _zEndOfNG2.match(s)
    if m and morphex(dDA, (iOffset+m.start(1), m.group(1)), ":[VR]", ":[NAQP]"):
        return True
    m = _zEndOfNG3.match(s)
    if m and not morph(dDA, (iOffset+m.start(1), m.group(1)), ":[NA]", False):
        return True
    return False


_zNextIsNotCOD1 = re.compile(" *,")
_zNextIsNotCOD2 = re.compile(" +(?:[mtsnj](e +|’)|[nv]ous |tu |ils? |elles? )")
_zNextIsNotCOD3 = re.compile(r" +([a-zéèî][\w-]+)")

def isNextNotCOD (dDA, s, iOffset):
    if _zNextIsNotCOD1.match(s) or _zNextIsNotCOD2.match(s):
        return True
    m = _zNextIsNotCOD3.match(s)
    if m and morphex(dDA, (iOffset+m.start(1), m.group(1)), ":[123][sp]", ":[DM]"):
        return True
    return False


_zNextIsVerb1 = re.compile(" +[nmts](?:e |’)")
_zNextIsVerb2 = re.compile(r" +(\w[\w-]+)")

def isNextVerb (dDA, s, iOffset):
    if _zNextIsVerb1.match(s):
        return True
    m = _zNextIsVerb2.match(s)
    if m and morph(dDA, (iOffset+m.start(1), m.group(1)), ":[123][sp]", False):
        return True
    return False


#### Exceptions

aREGULARPLURAL = frozenset(["abricot", "amarante", "aubergine", "acajou", "anthracite", "brique", "caca", "café", \
                            "carotte", "cerise", "chataigne", "corail", "citron", "crème", "grave", "groseille", \
                            "jonquille", "marron", "olive", "pervenche", "prune", "sable"])
aSHOULDBEVERB = frozenset(["aller", "manger"]) 


#### GRAMMAR CHECKING ENGINE PLUGIN

#### Check date validity

_lDay = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_dMonth = { "janvier":1, "février":2, "mars":3, "avril":4, "mai":5, "juin":6, "juillet":7, "août":8, "aout":8, "septembre":9, "octobre":10, "novembre":11, "décembre":12 }

import datetime


def checkDate (day, month, year):
    "to use if month is a number"
    try:
        return datetime.date(int(year), int(month), int(day))
    except ValueError:
        return False
    except:
        return True


def checkDateWithString (day, month, year):
    "to use if month is a noun"
    try:
        return datetime.date(int(year), _dMonth.get(month.lower(), ""), int(day))
    except ValueError:
        return False
    except:
        return True


def checkDay (weekday, day, month, year):
    "to use if month is a number"
    oDate = checkDate(day, month, year)
    if oDate and _lDay[oDate.weekday()] != weekday.lower():
        return False
    return True

def checkDayWithString (weekday, day, month, year):
    "to use if month is a noun"
    oDate = checkDate(day, _dMonth.get(month, ""), year)
    if oDate and _lDay[oDate.weekday()] != weekday.lower():
        return False
    return True


def getDay (day, month, year):
    "to use if month is a number"
    return _lDay[datetime.date(int(year), int(month), int(day)).weekday()]


def getDayWithString (day, month, year):
    "to use if month is a noun"
    return _lDay[datetime.date(int(year), _dMonth.get(month.lower(), ""), int(day)).weekday()]


#### GRAMMAR CHECKING ENGINE PLUGIN: Suggestion mechanisms

from . import conj
from . import mfsp
from . import phonet


## Verbs

def suggVerb (sFlex, sWho, funcSugg2=None):
    aSugg = set()
    for sStem in stem(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            # we get the tense
            aTense = set()
            for sMorph in _dAnalyses.get(sFlex, []): # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
                for m in re.finditer(">"+sStem+" .*?(:(?:Y|I[pqsf]|S[pq]|K|P))", sMorph):
                    # stem must be used in regex to prevent confusion between different verbs (e.g. sauras has 2 stems: savoir and saurer)
                    if m:
                        if m.group(1) == ":Y":
                            aTense.add(":Ip")
                            aTense.add(":Iq")
                            aTense.add(":Is")
                        elif m.group(1) == ":P":
                            aTense.add(":Ip")
                        else:
                            aTense.add(m.group(1))
            for sTense in aTense:
                if sWho == ":1ś" and not conj._hasConjWithTags(tTags, sTense, ":1ś"):
                    sWho = ":1s"
                if conj._hasConjWithTags(tTags, sTense, sWho):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, sTense, sWho))
    if funcSugg2:
        aSugg2 = funcSugg2(sFlex)
        if aSugg2:
            aSugg.add(aSugg2)
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggVerbPpas (sFlex, sWhat=None):
    aSugg = set()
    for sStem in stem(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            if not sWhat:
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q2"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q3"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q4"))
                aSugg.discard("")
            elif sWhat == ":m:s":
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sWhat == ":m:p":
                if conj._hasConjWithTags(tTags, ":PQ", ":Q2"):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q2"))
                else:
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sWhat == ":f:s":
                if conj._hasConjWithTags(tTags, ":PQ", ":Q3"):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q3"))
                else:
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sWhat == ":f:p":
                if conj._hasConjWithTags(tTags, ":PQ", ":Q4"):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q4"))
                else:
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sWhat == ":s":
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q3"))
                aSugg.discard("")
            elif sWhat == ":p":
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q2"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q4"))
                aSugg.discard("")
            else:
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggVerbTense (sFlex, sTense, sWho):
    aSugg = set()
    for sStem in stem(sFlex):
        if conj.hasConj(sStem, sTense, sWho):
            aSugg.add(conj.getConj(sStem, sTense, sWho))
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggVerbImpe (sFlex):
    aSugg = set()
    for sStem in stem(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            if conj._hasConjWithTags(tTags, ":E", ":2s"):
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":E", ":2s"))
            if conj._hasConjWithTags(tTags, ":E", ":1p"):
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":E", ":1p"))
            if conj._hasConjWithTags(tTags, ":E", ":2p"):
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":E", ":2p"))
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggVerbInfi (sFlex):
    return "|".join([ sStem  for sStem in stem(sFlex)  if conj.isVerb(sStem) ])


_dQuiEst = { "je": ":1s", "j’": ":1s", "j’en": ":1s", "j’y": ":1s", \
             "tu": ":2s", "il": ":3s", "on": ":3s", "elle": ":3s", "nous": ":1p", "vous": ":2p", "ils": ":3p", "elles": ":3p" }
_lIndicatif = [":Ip", ":Iq", ":Is", ":If"]
_lSubjonctif = [":Sp", ":Sq"]

def suggVerbMode (sFlex, cMode, sSuj):
    if cMode == ":I":
        lMode = _lIndicatif
    elif cMode == ":S":
        lMode = _lSubjonctif
    elif cMode.startswith((":I", ":S")):
        lMode = [cMode]
    else:
        return ""
    sWho = _dQuiEst.get(sSuj.lower(), None)
    if not sWho:
        if sSuj[0:1].islower(): # pas un pronom, ni un nom propre
            return ""
        sWho = ":3s"
    aSugg = set()
    for sStem in stem(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            for sTense in lMode:
                if conj._hasConjWithTags(tTags, sTense, sWho):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, sTense, sWho))
    if aSugg:
        return "|".join(aSugg)
    return ""


## Nouns and adjectives

def suggPlur (sFlex, sWordToAgree=None):
    "returns plural forms assuming sFlex is singular"
    if sWordToAgree:
        if sWordToAgree not in _dAnalyses and not _storeMorphFromFSA(sWordToAgree):
            return ""
        sGender = cr.getGender(_dAnalyses.get(sWordToAgree, []))
        if sGender == ":m":
            return suggMasPlur(sFlex)
        elif sGender == ":f":
            return suggFemPlur(sFlex)
    aSugg = set()
    if "-" not in sFlex:
        if sFlex.endswith("l"):
            if sFlex.endswith("al") and len(sFlex) > 2 and _oSpellChecker.isValid(sFlex[:-1]+"ux"):
                aSugg.add(sFlex[:-1]+"ux")
            if sFlex.endswith("ail") and len(sFlex) > 3 and _oSpellChecker.isValid(sFlex[:-2]+"ux"):
                aSugg.add(sFlex[:-2]+"ux")
        if _oSpellChecker.isValid(sFlex+"s"):
            aSugg.add(sFlex+"s")
        if _oSpellChecker.isValid(sFlex+"x"):
            aSugg.add(sFlex+"x")
    if mfsp.hasMiscPlural(sFlex):
        aSugg.update(mfsp.getMiscPlural(sFlex))
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggSing (sFlex):
    "returns singular forms assuming sFlex is plural"
    if "-" in sFlex:
        return ""
    aSugg = set()
    if sFlex.endswith("ux"):
        if _oSpellChecker.isValid(sFlex[:-2]+"l"):
            aSugg.add(sFlex[:-2]+"l")
        if _oSpellChecker.isValid(sFlex[:-2]+"il"):
            aSugg.add(sFlex[:-2]+"il")
    if _oSpellChecker.isValid(sFlex[:-1]):
        aSugg.add(sFlex[:-1])
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggMasSing (sFlex, bSuggSimil=False):
    "returns masculine singular forms"
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = set()
    for sMorph in _dAnalyses.get(sFlex, []):
        if not ":V" in sMorph:
            # not a verb
            if ":m" in sMorph or ":e" in sMorph:
                aSugg.add(suggSing(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isFemForm(sStem):
                    aSugg.update(mfsp.getMasForm(sStem, False))
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q1") and conj.hasConj(sVerb, ":PQ", ":Q3"):
                # We also check if the verb has a feminine form.
                # If not, we consider it’s better to not suggest the masculine one, as it can be considered invariable.
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q1"))
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":m:[si]"):
            aSugg.add(e)
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggMasPlur (sFlex, bSuggSimil=False):
    "returns masculine plural forms"
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = set()
    for sMorph in _dAnalyses.get(sFlex, []):
        if not ":V" in sMorph:
            # not a verb
            if ":m" in sMorph or ":e" in sMorph:
                aSugg.add(suggPlur(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isFemForm(sStem):
                    aSugg.update(mfsp.getMasForm(sStem, True))
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q2"):
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q2"))
            elif conj.hasConj(sVerb, ":PQ", ":Q1"):
                sSugg = conj.getConj(sVerb, ":PQ", ":Q1")
                # it is necessary to filter these flexions, like “succédé” or “agi” that are not masculine plural.
                if sSugg.endswith("s"):
                    aSugg.add(sSugg)
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":m:[pi]"):
            aSugg.add(e)
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggFemSing (sFlex, bSuggSimil=False):
    "returns feminine singular forms"
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = set()
    for sMorph in _dAnalyses.get(sFlex, []):
        if not ":V" in sMorph:
            # not a verb
            if ":f" in sMorph or ":e" in sMorph:
                aSugg.add(suggSing(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isFemForm(sStem):
                    aSugg.add(sStem)
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q3"):
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q3"))
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":f:[si]"):
            aSugg.add(e)
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggFemPlur (sFlex, bSuggSimil=False):
    "returns feminine plural forms"
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = set()
    for sMorph in _dAnalyses.get(sFlex, []):
        if not ":V" in sMorph:
            # not a verb
            if ":f" in sMorph or ":e" in sMorph:
                aSugg.add(suggPlur(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isFemForm(sStem):
                    aSugg.add(sStem+"s")
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q4"):
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q4"))
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":f:[pi]"):
            aSugg.add(e)
    if aSugg:
        return "|".join(aSugg)
    return ""


def hasFemForm (sFlex):
    for sStem in stem(sFlex):
        if mfsp.isFemForm(sStem) or conj.hasConj(sStem, ":PQ", ":Q3"):
            return True
    if phonet.hasSimil(sFlex, ":f"):
        return True
    return False


def hasMasForm (sFlex):
    for sStem in stem(sFlex):
        if mfsp.isFemForm(sStem) or conj.hasConj(sStem, ":PQ", ":Q1"):
            # what has a feminine form also has a masculine form
            return True
    if phonet.hasSimil(sFlex, ":m"):
        return True
    return False


def switchGender (sFlex, bPlur=None):
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = set()
    if bPlur == None:
        for sMorph in _dAnalyses.get(sFlex, []):
            if ":f" in sMorph:
                if ":s" in sMorph:
                    aSugg.add(suggMasSing(sFlex))
                elif ":p" in sMorph:
                    aSugg.add(suggMasPlur(sFlex))
            elif ":m" in sMorph:
                if ":s" in sMorph:
                    aSugg.add(suggFemSing(sFlex))
                elif ":p" in sMorph:
                    aSugg.add(suggFemPlur(sFlex))
                else:
                    aSugg.add(suggFemSing(sFlex))
                    aSugg.add(suggFemPlur(sFlex))
    elif bPlur:
        for sMorph in _dAnalyses.get(sFlex, []):
            if ":f" in sMorph:
                aSugg.add(suggMasPlur(sFlex))
            elif ":m" in sMorph:
                aSugg.add(suggFemPlur(sFlex))
    else:
        for sMorph in _dAnalyses.get(sFlex, []):
            if ":f" in sMorph:
                aSugg.add(suggMasSing(sFlex))
            elif ":m" in sMorph:
                aSugg.add(suggFemSing(sFlex))
    if aSugg:
        return "|".join(aSugg)
    return ""


def switchPlural (sFlex):
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = set()
    for sMorph in _dAnalyses.get(sFlex, []):
        if ":s" in sMorph:
            aSugg.add(suggPlur(sFlex))
        elif ":p" in sMorph:
            aSugg.add(suggSing(sFlex))
    if aSugg:
        return "|".join(aSugg)
    return ""


def hasSimil (sWord, sPattern=None):
    return phonet.hasSimil(sWord, sPattern)


def suggSimil (sWord, sPattern=None, bSubst=False):
    "return list of words phonetically similar to sWord and whom POS is matching sPattern"
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    aSugg = phonet.selectSimil(sWord, sPattern)
    for sMorph in _dAnalyses.get(sWord, []):
        aSugg.update(conj.getSimil(sWord, sMorph, bSubst))
        break
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggCeOrCet (sWord):
    if re.match("(?i)[aeéèêiouyâîï]", sWord):
        return "cet"
    if sWord[0:1] == "h" or sWord[0:1] == "H":
        return "ce|cet"
    return "ce"


def suggLesLa (sWord):
    # we don’t check if word exists in _dAnalyses, for it is assumed it has been done before
    if any( ":p" in sMorph  for sMorph in _dAnalyses.get(sWord, []) ):
        return "les|la"
    return "la"


_zBinary = re.compile("^[01]+$")

def formatNumber (s):
    nLen = len(s)
    if nLen < 4:
        return s
    sRes = ""
    # nombre ordinaire
    nEnd = nLen
    while nEnd > 0:
        nStart = max(nEnd-3, 0)
        sRes = s[nStart:nEnd] + " " + sRes  if sRes  else s[nStart:nEnd]
        nEnd = nEnd - 3
    # binaire
    if _zBinary.search(s):
        nEnd = nLen
        sBin = ""
        while nEnd > 0:
            nStart = max(nEnd-4, 0)
            sBin = s[nStart:nEnd] + " " + sBin  if sBin  else s[nStart:nEnd]
            nEnd = nEnd - 4
        sRes += "|" + sBin
    # numéros de téléphone
    if nLen == 10:
        if s.startswith("0"):
            sRes += "|" + s[0:2] + " " + s[2:4] + " " + s[4:6] + " " + s[6:8] + " " + s[8:] # téléphone français
            if s[1] == "4" and (s[2]=="7" or s[2]=="8" or s[2]=="9"):
                sRes += "|" + s[0:4] + " " + s[4:6] + " " + s[6:8] + " " + s[8:]            # mobile belge
            sRes += "|" + s[0:3] + " " + s[3:6] + " " + s[6:8] + " " + s[8:]                # téléphone suisse
        sRes += "|" + s[0:4] + " " + s[4:7] + "-" + s[7:]                                   # téléphone canadien ou américain
    elif nLen == 9 and s.startswith("0"):
        sRes += "|" + s[0:3] + " " + s[3:5] + " " + s[5:7] + " " + s[7:9]                   # fixe belge 1
        sRes += "|" + s[0:2] + " " + s[2:5] + " " + s[5:7] + " " + s[7:9]                   # fixe belge 2
    return sRes


def formatNF (s):
    try:
        m = re.match("NF[  -]?(C|E|P|Q|S|X|Z|EN(?:[  -]ISO|))[  -]?([0-9]+(?:[/‑-][0-9]+|))", s)
        if not m:
            return ""
        return "NF " + m.group(1).upper().replace(" ", " ").replace("-", " ") + " " + m.group(2).replace("/", "‑").replace("-", "‑")
    except:
        traceback.print_exc()
        return "# erreur #"


def undoLigature (c):
    if c == "ﬁ":
        return "fi"
    elif c == "ﬂ":
        return "fl"
    elif c == "ﬀ":
        return "ff"
    elif c == "ﬃ":
        return "ffi"
    elif c == "ﬄ":
        return "ffl"
    elif c == "ﬅ":
        return "ft"
    elif c == "ﬆ":
        return "st"
    return "_"




_xNormalizedCharsForInclusiveWriting = str.maketrans({
    '(': '_',  ')': '_',
    '.': '_',  '·': '_',
    '–': '_',  '—': '_',
    '/': '_'
 })


def normalizeInclusiveWriting (sToken):
    return sToken.translate(_xNormalizedCharsForInclusiveWriting)



# generated code, do not edit
def p_p_URL2_1 (s, m):
    return m.group(1).capitalize()
def p_p_sigle1_1 (s, m):
    return m.group(1).replace(".", "")+"."
def c_p_sigle2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search(r"(?i)^(?:i\.e\.|s\.[tv]\.p\.|e\.g\.|a\.k\.a\.|c\.q\.f\.d\.|b\.a\.|n\.b\.)$", m.group(0))
def c_p_sigle2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).__len__() == 4
def s_p_sigle2_2 (s, m):
    return m.group(0).replace(".", "").upper() + "|" + m.group(0)[0:2] + " " + m.group(0)[2:4]
def c_p_sigle2_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_p_sigle2_3 (s, m):
    return m.group(0).replace(".", "").upper()
def c_p_sigle2_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0) != "b.a."
def p_p_sigle2_4 (s, m):
    return m.group(0).replace(".", "_")
def p_p_sigle3_1 (s, m):
    return m.group(0).replace(".", "").replace("-","")
def c_p_points_suspension_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^etc", m.group(1))
def c_p_prénom_lettre_point_patronyme_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M[12]", False) and (morph(dDA, (m.start(3), m.group(3)), ":(?:M[12]|V)", False) or not _oSpellChecker.isValid(m.group(3)))
def c_p_prénom_lettre_point_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M[12]", False) and look(s[m.end():], "^\W+[a-zéèêîïâ]")
def p_p_patronyme_composé_avec_le_la_les_1 (s, m):
    return m.group(0).replace(" ", "_")
def c_p_mot_entre_crochets_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).isdigit()
def c_p_mot_entre_crochets_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(1), m.group(1)), ":G", False)
def p_p_mot_entre_crochets_2 (s, m):
    return " " + m.group(1) + " "
def c_p_mot_entre_crochets_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_typo_écriture_épicène_tous_toutes_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo")
def p_typo_écriture_épicène_tous_toutes_2 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_ceux_celles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo")
def p_typo_écriture_épicène_ceux_celles_2 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_pluriel_eur_divers_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo") and m.group(2) != "se"
def c_typo_écriture_épicène_pluriel_eur_divers_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo") and m.group(2) == "se"
def p_typo_écriture_épicène_pluriel_eur_divers_3 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_pluriel_eux_euses_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo")
def p_typo_écriture_épicène_pluriel_eux_euses_2 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_pluriel_aux_ales_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo")
def p_typo_écriture_épicène_pluriel_aux_ales_2 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_pluriel_er_ère_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo")
def p_typo_écriture_épicène_pluriel_er_ère_2 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_pluriel_if_ive_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo")
def p_typo_écriture_épicène_pluriel_if_ive_2 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def p_typo_écriture_épicène_pluriel_e_1 (s, m):
    return normalizeInclusiveWriting(m.group(0))
def c_typo_écriture_épicène_pluriel_e_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo") and not m.group(0).endswith("les")
def c_typo_écriture_épicène_pluriel_e_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("s") and not m.group(0).endswith("·e·s")
def c_typo_écriture_épicène_pluriel_e_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and not m.group(0).endswith("e·s")
def c_typo_écriture_épicène_singulier_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("typo") and (m.group(1) == "un" or m.group(1) == "Un")
def c_typo_écriture_épicène_singulier_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and option("typo") and not m.group(0).endswith("·e")
def c_majuscule_après_point_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:etc|[A-Z]|chap|cf|fig|hab|litt|circ|coll|r[eé]f|étym|suppl|bibl|bibliogr|cit|op|vol|déc|nov|oct|janv|juil|avr|sept)$", m.group(1)) and morph(dDA, (m.start(1), m.group(1)), ":", False) and morph(dDA, (m.start(2), m.group(2)), ":", False)
def s_majuscule_après_point_1 (s, m):
    return m.group(2).capitalize()
def c_majuscule_en_début_phrase_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "\w\w[.] +\w+")
def s_majuscule_en_début_phrase_1 (s, m):
    return m.group(1).capitalize()
def c_virgule_manquante_avant_car_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":[DR]", False)
def c_virg_virgule_après_point_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^(?:etc|[A-Z]|fig|hab|litt|circ|coll|ref|étym|suppl|bibl|bibliogr|cit|vol|déc|nov|oct|janv|juil|avr|sept|pp?)$", m.group(1))
def c_typo_espace_manquant_après1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1).isdigit()
def c_typo_espace_manquant_après3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (m.group(1).__len__() > 1 and not m.group(1).isdigit() and _oSpellChecker.isValid(m.group(1))) or look(s[m.end():], "^’")
def s_typo_point_après_titre_1 (s, m):
    return m.group(1)[0:-1]
def s_typo_point_après_numéro_1 (s, m):
    return "nᵒˢ"  if m.group(1)[1:3] == "os"  else "nᵒ"
def c_typo_points_suspension1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "(?i)etc$")
def s_typo_points_suspension2_1 (s, m):
    return m.group(0).replace("...", "…").rstrip(".")
def s_typo_ponctuation_superflue1_1 (s, m):
    return ",|" + m.group(1)
def s_typo_ponctuation_superflue2_1 (s, m):
    return ";|" + m.group(1)
def s_typo_ponctuation_superflue3_1 (s, m):
    return ":|" + m.group(0)[1]
def c_nbsp_ajout_avant_double_ponctuation_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return sCountry != "CA"
def s_nbsp_ajout_avant_double_ponctuation_1 (s, m):
    return " "+m.group(0)
def c_typo_signe_multiplication_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(0).startswith("0x")
def s_ligatures_typographiques_1 (s, m):
    return undoLigature(m.group(0))
def c_typo_apostrophe_incorrecte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (m.group(2).__len__() == 1  and  m.group(1).endswith("′ "))
def s_typo_apostrophe_manquante_prudence1_1 (s, m):
    return m.group(1)[:-1]+"’"
def c_typo_apostrophe_manquante_prudence2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not option("mapos") and morph(dDA, (m.start(2), m.group(2)), ":V", False)
def s_typo_apostrophe_manquante_prudence2_1 (s, m):
    return m.group(1)[:-1]+"’"
def c_typo_apostrophe_manquante_audace1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("mapos") and not look(s[:m.start()], "(?i)(?:lettre|caractère|glyphe|dimension|variable|fonction|point) *$")
def s_typo_apostrophe_manquante_audace1_1 (s, m):
    return m.group(1)[:-1]+"’"
def c_typo_guillemets_typographiques_doubles_ouvrants_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"[a-zA-Zéïîùàâäôö]$")
def c_typo_élision_déterminants_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:onz[ei]|énième|iourte|ouistiti|ouate|one-?step|ouf|Ouagadougou|I(?:I|V|X|er|ᵉʳ|ʳᵉ|è?re))", m.group(2)) and not m.group(2).isupper() and not morph(dDA, (m.start(2), m.group(2)), ":G", False)
def s_typo_élision_déterminants_1 (s, m):
    return m.group(1)[0]+"’"
def c_typo_euphonie_cet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:onz|énième|ouf|énième|ouistiti|one-?step|I(?:I|V|X|er|ᵉʳ))", m.group(2)) and morph(dDA, (m.start(2), m.group(2)), ":[me]")
def c_nf_norme_française_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^NF (?:C|E|P|Q|S|X|Z|EN(?: ISO|)) [0-9]+(?:‑[0-9]+|)", m.group(0))
def s_nf_norme_française_1 (s, m):
    return formatNF(m.group(0))
def s_chim_molécules_1 (s, m):
    return m.group(0).replace("2", "₂").replace("3", "₃").replace("4", "₄")
def c_typo_cohérence_guillemets_chevrons_ouvrants_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\w$")
def c_typo_cohérence_guillemets_chevrons_ouvrants_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], r"^\w")
def c_typo_cohérence_guillemets_chevrons_fermants_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\w$")
def c_typo_cohérence_guillemets_chevrons_fermants_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], r"^\w")
def c_typo_cohérence_guillemets_doubles_ouvrants_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\w$")
def c_typo_cohérence_guillemets_doubles_fermants_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\w$")
def c_typo_cohérence_guillemets_doubles_fermants_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], r"^\w")
def c_typo_guillemet_simple_ouvrant_non_fermé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r" $") or look(s[:m.start()], "^ *$|, *$")
def c_typo_guillemet_simple_fermant_non_ouvert_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "^ ") or look(s[m.end():], "^ *$|^,")
def c_unit_nbsp_avant_unités2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ";S", ":[VCR]") or mbUnit(m.group(3)) or not _oSpellChecker.isValid(m.group(3))
def c_unit_nbsp_avant_unités3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (m.group(2).__len__() > 4 and not _oSpellChecker.isValid(m.group(3))) or morphex(dDA, (m.start(3), m.group(3)), ";S", ":[VCR]") or mbUnit(m.group(3))
def c_num_grand_nombre_soudé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "NF[  -]?(C|E|P|Q|X|Z|EN(?:[  -]ISO|)) *$")
def c_num_grand_nombre_soudé_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).__len__() > 4
def s_num_grand_nombre_soudé_2 (s, m):
    return formatNumber(m.group(0))
def c_num_grand_nombre_soudé_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and look(s[m.end():], "^(?:,\d+[⁰¹²³⁴⁵⁶⁷⁸⁹]?|[⁰¹²³⁴⁵⁶⁷⁸⁹])") or look(s[m.end():], r"^[   ]*(?:[kcmµn]?(?:[slgJKΩ]|m[²³]?|Wh?|Hz|dB)|[%‰€$£¥Åℓhj]|min|°C|℃)(?![\w’'])")
def s_num_grand_nombre_soudé_3 (s, m):
    return formatNumber(m.group(0))
def c_num_nombre_quatre_chiffres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ";S", ":[VCR]") or mbUnit(m.group(2))
def s_num_nombre_quatre_chiffres_1 (s, m):
    return formatNumber(m.group(1))
def c_num_grand_nombre_avec_points_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("num")
def s_num_grand_nombre_avec_points_1 (s, m):
    return m.group(0).replace(".", " ")
def p_num_grand_nombre_avec_points_2 (s, m):
    return m.group(0).replace(".", "_")
def c_num_grand_nombre_avec_espaces_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("num")
def s_num_grand_nombre_avec_espaces_1 (s, m):
    return m.group(0).replace(" ", " ")
def p_num_grand_nombre_avec_espaces_2 (s, m):
    return m.group(0).replace(" ", "_")
def c_date_nombres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not checkDate(m.group(1), m.group(2), m.group(3)) and not look(s[:m.start()], r"(?i)\bversions? +$")
def p_date_nombres_2 (s, m):
    return m.group(0).replace(".", "-").replace(" ", "-").replace("\/", "-")
def c_redondances_paragraphe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":(?:G|V0)|>(?:t(?:antôt|emps|rès)|loin|souvent|parfois|quelquefois|côte|petit|même) ", False) and not m.group(1)[0].isupper()
def c_redondances_paragraphe_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def p_p_trait_union_conditionnel1_1 (s, m):
    return m.group(0).replace("‑", "")
def p_p_trait_union_conditionnel2_1 (s, m):
    return m.group(0).replace("‑", "")
def c_doublon_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^([nv]ous|faire|en|la|lui|donnant|œuvre|h[éoa]|hou|olé|joli|Bora|couvent|dément|sapiens|très|vroum|[0-9]+)$", m.group(1)) and not (re.search("^(?:est|une?)$", m.group(1)) and look(s[:m.start()], "[’']$")) and not (m.group(1) == "mieux" and look(s[:m.start()], "(?i)qui +$"))
def c_num_lettre_O_zéro1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not option("ocr")
def s_num_lettre_O_zéro1_1 (s, m):
    return m.group(0).replace("O", "0")
def c_num_lettre_O_zéro2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not option("ocr")
def s_num_lettre_O_zéro2_1 (s, m):
    return m.group(0).replace("O", "0")
def s_typo_ordinaux_premier_1 (s, m):
    return m.group(0).replace(" ", "").replace("è", "").replace("i", "").replace("e", "ᵉ").replace("r", "ʳ").replace("s", "ˢ")
def s_typo_ordinaux_deuxième_1 (s, m):
    return m.group(0).replace(" ", "").replace("n", "").replace("d", "ᵈ").replace("e", "ᵉ").replace("s", "ˢ")
def c_typo_ordinaux_nième_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s")
def c_typo_ordinaux_nième_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_typo_ordinaux_romain_premier_1 (s, m):
    return m.group(0).replace(" ", "").replace("è", "").replace("i", "").replace("e", "ᵉ").replace("r", "ʳ").replace("s", "ˢ")
def s_typo_ordinaux_romain_deuxième_1 (s, m):
    return m.group(0).replace(" ", "").replace("n", "").replace("d", "ᵈ").replace("e", "ᵉ").replace("s", "ˢ")
def c_typo_ordinaux_romains_nième_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(0), m.group(0)), ":G", False)
def c_typo_ordinaux_romains_nième_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s")
def c_typo_ordinaux_romains_nième_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_d_typo_écriture_épicène_pluriel_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":G")
def d_d_typo_écriture_épicène_pluriel_1 (s, m, dDA):
    return define(dDA, m.start(1), [":N:A:Q:e:p"])
def c_d_typo_écriture_épicène_singulier_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False)
def d_d_typo_écriture_épicène_singulier_1 (s, m, dDA):
    return define(dDA, m.start(1), [":N:A:Q:e:s"])
def c_date_jour_mois_année_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not checkDateWithString(m.group(1), m.group(2), m.group(3))
def c_date_journée_jour_mois_année1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], r"^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(m.group(1), m.group(2), m.group(3), m.group(4))
def s_date_journée_jour_mois_année1_1 (s, m):
    return getDay(m.group(2), m.group(3), m.group(4))
def c_date_journée_jour_mois_année2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], r"^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDayWithString(m.group(1), m.group(2), m.group(3), m.group(4))
def s_date_journée_jour_mois_année2_1 (s, m):
    return getDayWithString(m.group(2), m.group(3), m.group(4))
def c_p_références_aux_notes_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(0), m.group(0)), ":", False)
def c_p_pas_mal_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False)
def c_p_pas_assez_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":A", False) and not morph(dDA, prevword1(s, m.start()), ":D", False)
def c_p_titres_et_ordinaux_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "I"
def c_p_fusion_mots_multiples_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(0).replace(" ", "_"))
def p_p_fusion_mots_multiples_1 (s, m):
    return m.group(0).replace(" ", "_")
def c_tu_t_euphonique_incorrect_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return re.search("(?i)^(?:ils|elles|tu)$", m.group(2))
def c_tu_t_euphonique_incorrect_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(1) != "-t-" and m.group(1) != "-T-"
def c_tu_trait_union_douteux_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(1)+"-"+m.group(2)) and analyse(m.group(1)+"-"+m.group(2), ":", False)
def c_tu_ce_cette_ces_nom_là1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NB]", False)
def c_tu_ce_cette_ces_nom_là2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NB]", False) and look(s[m.end():], "^ *$|^,")
def c_tu_préfixe_ex_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":N") and not re.search("(?i)^(?:aequo|nihilo|cathedra|absurdo|abrupto)", m.group(1))
def c_tu_préfixe_mi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False)
def c_tu_préfixe_quasi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":N", ":[AGW]")
def c_tu_préfixe_semi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":G")
def c_tu_préfixe_xxxo_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(1)+"-"+m.group(2)) and analyse(m.group(1)+"-"+m.group(2), ":", False)
def c_tu_préfixe_pseudo_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":N")
def c_tu_préfixe_pseudo_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_tu_préfixe_divers_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(1)+"-"+m.group(2)) and analyse(m.group(1)+"-"+m.group(2), ":", False) and morph(dDA, prevword1(s, m.start()), ":D", False, not bool(re.search("(?i)^(?:s(?:ans|ous)|non)$", m.group(1))))
def c_tu_mots_composés_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(1)+"-"+m.group(2)) and analyse(m.group(1)+"-"+m.group(2), ":N", False) and morph(dDA, prevword1(s, m.start()), ":(?:D|V0e)", False, True) and not (morph(dDA, (m.start(1), m.group(1)), ":G", False) and morph(dDA, (m.start(2), m.group(2)), ":[GYB]", False))
def s_tu_aller_retour_1 (s, m):
    return m.group(0).replace(" ", "-")
def s_tu_arc_en_ciel_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_tu_bouche_à_oreille_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":D", False)
def s_tu_bouche_à_oreille_1 (s, m):
    return m.group(0).replace(" ", "-")
def s_tu_celui_celle_là_ci_1 (s, m):
    return m.group(0).replace(" ", "-").replace("si", "ci")
def s_tu_grand_père_mère_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_tu_nord_sud_est_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "^ *$|^,")
def c_tu_ouï_dire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":G")
def c_tu_prêt_à_porter_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)\b(?:les?|du|des|un|ces?|[mts]on) +")
def s_tu_stock_option_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_tu_soi_disant_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not ( morph(dDA, prevword1(s, m.start()), ":R", False) and look(s[m.end():], "^ +qu[e’]") )
def c_tu_est_ce_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":N.*:[me]:[si]|>qui ") and morph(dDA, prevword1(s, m.start()), ":Cs", False, True)
def c_tu_pronom_même_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], "^ +s(?:i |’)")
def s_tu_nombres_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_tu_nombres_vingt_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "(?i)quatre $")
def s_tu_nombres_vingt_1 (s, m):
    return m.group(0).replace(" ", "-").replace("vingts", "vingt")
def s_tu_nombres_soixante_1 (s, m):
    return m.group(0).replace(" ", "-")
def s_tu_nombres_octante_1 (s, m):
    return m.group(0).replace(" ", "-").replace("vingts", "vingt")
def s_tu_s_il_te_plaît_1 (s, m):
    return m.group(0).replace("-", " ")
def c_tu_trois_quarts_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def s_tu_parce_que_1 (s, m):
    return m.group(0).replace("-", " ")
def s_tu_qqch_ça_aussi_donc_1 (s, m):
    return m.group(0).replace("-", " ")
def s_tu_d_entre_pronom_1 (s, m):
    return m.group(0).replace("-", " ")
def c_tu_y_attaché_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0|>en ", False)
def c_tu_lorsque_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\bd[eè]s +$")
def s_tu_lorsque_1 (s, m):
    return m.group(0).replace(" ", "")
def c_virgule_dialogue_après_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":M", ":G") and not morph(dDA, (m.start(2), m.group(2)), ":N", False) and look(s[:m.start()], "^ *$|, *$")
def c_virgule_dialogue_avant_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":E", False) and morph(dDA, (m.start(3), m.group(3)), ":M", False)
def c_virgule_après_verbe_COD_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":M", False) and not morph(dDA, prevword1(s, m.start()), ">à ", False, False)
def c_typo_apostrophe_manquante_audace2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return option("mapos")
def s_typo_apostrophe_manquante_audace2_1 (s, m):
    return m.group(1)[:-1]+"’"
def c_typo_À_début_phrase1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[GNAY]", ":(?:Q|3s)|>(?:priori|post[eé]riori|contrario|capella|fortiori) ") or (m.group(2) == "bientôt" and look(s[m.end():], "^ *$|^,"))
def s_maj_accents_1 (s, m):
    return "É"+m.group(0)[0:1]
def p_maj_accents_2 (s, m):
    return "É"+m.group(0)[0:1]
def c_d_dans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:p|>[a-z]+ièmes ", False, False)
def d_d_dans_1 (s, m, dDA):
    return select(dDA, m.start(0), m.group(0), ":R")
def c_d_ton_son_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:le|ce[st]?|ton|mon|son|quel(?:que|)s?|[nv]otre|un|leur|ledit|dudit) ")
def d_d_ton_son_1 (s, m, dDA):
    return exclude(dDA, m.start(2), m.group(2), ":D")
def c_d_je_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":1s", False, False)
def d_d_je_le_la_les_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def c_d_tu_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":2s", False, False)
def d_d_tu_le_la_les_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def c_d_il_elle_on_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":3s", False, False)
def d_d_il_elle_on_le_la_les_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def c_d_nous_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":1p", False, False)
def d_d_nous_le_la_les_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def c_d_vous_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":2p", False, False)
def d_d_vous_le_la_les_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def c_d_nous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":1p", False)
def d_d_nous_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":Os")
def c_d_vous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":2p", False)
def d_d_vous_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":Os")
def c_d_ils_elles_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":3p", False, False)
def d_d_ils_elles_le_la_les_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def d_d_ne_me_te_te_le_la_leur_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":Oo")
def c_d_ne_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":(?:O[sp]|X)", False)
def d_d_ne_verbe_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":V")
def c_d_n_m_t_s_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":X", False)
def d_d_n_m_t_s_verbe_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":V")
def d_d_me_te_se_verbe_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":V")
def d_d_je_verbe_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":[123][sp]")
def c_d_je_il_ils_on_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":(?:Oo|X)", False)
def d_d_je_il_ils_on_verbe_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":[123][sp]")
def c_d_tu_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":Cs", False, True) and not morph(dDA, (m.start(1), m.group(1)), ":(?:Oo|X)", False)
def d_d_tu_verbe_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":[123][sp]")
def c_d_nom_propre_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M") and m.group(2).islower() and morphex(dDA, (m.start(2), m.group(2)), ":[123][sg]", ":Q") and morph(dDA, (m.start(2), m.group(2)), ":N", False) and morph(dDA, prevword1(s, m.start()), ":Cs", False, True)
def d_d_nom_propre_verbe_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":[123][sp]")
def c_d_nom_propre_verbe_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M", False) and morphex(dDA, (m.start(2), m.group(2)), ":[123]s|>(?:[nmts]e|nous|vous) ", ":A") and look(s[:m.start()], "^ *$|, *$")
def d_d_nom_propre_verbe_2 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":M")
def d_d_que_combien_pourquoi_en_y_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":E")
def c_d_aucun_non_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NA].*:[me]", False)
def d_d_aucun_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V")
def c_d_de_non_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":[YD]", False)
def d_d_de_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V")
def d_d_d_un_une_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V")
def d_d_déterminant_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V")
def c_d_de_la_non_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":Y", False)
def d_d_de_la_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V")
def d_d_de_pronom_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V")
def d_d_par_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":V[123]")
def d_d_très_non_verbe_1 (s, m, dDA):
    return exclude(dDA, m.start(1), m.group(1), ":[123][sp]")
def d_p_bac_plus_nombre_2 (s, m, dDA):
    return define(dDA, m.start(0), [":N:e:i"])
def c_ocr_point_interrogation_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(sx[m.end():], "^(?: +[A-ZÉÈÂ(]|…|[.][.]+| *$)")
def c_ocr_virgules_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not sx[m.start():m.end()].endswith("…")
def s_ocr_virgules_1 (s, m):
    return m.group(0)[:-1]
def c_ocr_nombres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0) == "II"
def c_ocr_nombres_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and not m.group(0).isdigit()
def s_ocr_nombres_2 (s, m):
    return m.group(0).replace("O", "0").replace("I", "1")
def s_ocr_age_1 (s, m):
    return m.group(0).replace("a", "â").replace("A", "Â")
def s_ocr_autre_1 (s, m):
    return m.group(0).replace("n", "u")
def c_ocr_chère_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b([jnlmts]’|il |on |elle )$")
def c_ocr_celui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b[jn]e +$")
def c_ocr_cette1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":N.*:f:s", False)
def c_ocr_cette2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:f:[si]")
def c_ocr_comme_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ">(?:et|o[uù]) ")
def c_ocr_contre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^contre$", m.group(0))
def c_ocr_dans1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:p", False, False)
def c_ocr_dans2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:p", False, False)
def s_ocr_dame_1 (s, m):
    return m.group(0).replace("rn", "m")
def c_ocr_de_des1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("é") and not morph(dDA, prevword1(s, m.start()), ":D.*:m:[si]", False, False)
def c_ocr_de_des1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s") and not morph(dDA, prevword1(s, m.start()), ":D.*:m:p", False, False)
def c_ocr_de_des2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("o")
def c_ocr_de_des2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and not morph(dDA, prevword1(s, m.start()), ":D.*:[me]", False, False)
def c_ocr_de_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\bau ")
def c_ocr_du_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NA]:[me]:[si]", ":Y")
def c_ocr_elle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("e") and ( morph(dDA, prevword1(s, m.start()), ":R", False, True) or isNextVerb(dDA, s[m.end():], m.end()) )
def c_ocr_elle_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s") and ( morph(dDA, prevword1(s, m.start()), ":R", False, True) or isNextVerb(dDA, s[m.end():], m.end()) )
def c_ocr_et_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "[0-9] +$")
def c_ocr_état_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("l")
def c_ocr_état_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_ocr_il_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and morph(dDA, (m.start(2), m.group(2)), ":(?:O[on]|3s)", False)
def c_ocr_il_ils2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s")
def c_ocr_il_ils2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_ocr_il_ils3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(0).endswith("s")
def c_ocr_il_ils3_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_ocr_large_1 (s, m):
    return m.group(0).replace("o", "e")
def c_ocr_lj1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)\w") or not morph(dDA, (m.start(2), m.group(2)), ":Y", False)
def c_ocr_exclamation2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ";S", False) and not morph(dDA, prevword1(s, m.start()), ":R", False)
def c_ocr_lv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).istitle() and look(s[:m.start()], r"(?i)\w") and morphex(dDA, (m.start(0), m.group(0)), ":", ":M")
def c_ocr_lv_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(1))
def c_ocr_lv_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_ocr_lp_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)\w") and morphex(dDA, (m.start(0), m.group(0)), ":", ":M") and _oSpellChecker.isValid(m.group(1))
def c_ocr_l_était_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)\w")
def s_ocr_le_les_1 (s, m):
    return m.group(0).replace("é", "e").replace("É", "E")
def c_ocr_le_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("e")
def c_ocr_le_la_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(0).endswith("a")
def c_ocr_le_la_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(0).endswith("à")
def c_ocr_le_la_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_ocr_tu_le_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":(?:V0|N.*:m:[si])", False, False)
def c_ocr_mais2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D:[me]:p", False, False)
def c_ocr_mais3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D:(?:m:s|e:p)", False, False)
def c_ocr_mais4_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ">(?:homme|ce|quel|être) ", False, False)
def c_ocr_même1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("e") and not morph(dDA, prevword1(s, m.start()), ":D.*:[me]:[si]", False, False)
def c_ocr_même1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s") and not morph(dDA, prevword1(s, m.start()), ":D.*:[me]:[pi]", False, False)
def s_ocr_même2_1 (s, m):
    return m.group(0).replace("è", "ê").replace("È", "Ê")
def s_ocr_même3_1 (s, m):
    return m.group(0).replace("é", "ê").replace("É", "Ê")
def s_ocr_mot_1 (s, m):
    return m.group(0).replace("l", "t").replace("L", "T")
def c_ocr_par_le_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:ne|il|on|elle|je) +$") and morph(dDA, (m.start(2), m.group(2)), ":[NA].*:[me]:[si]", False)
def c_ocr_par_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:ne|il|on|elle) +$") and morph(dDA, (m.start(2), m.group(2)), ":[NA].*:[fe]:[si]", False)
def c_ocr_par_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:ne|tu) +$") and morph(dDA, (m.start(2), m.group(2)), ":[NA].*:[pi]", False)
def c_ocr_peu_peux_peut_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("u") and not morph(dDA, prevword1(s, m.start()), ":D.*:m:s", False, False)
def c_ocr_peu_peux_peut_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("x") and not morph(dDA, prevword1(s, m.start()), ":D.*:m:p", False, False)
def c_ocr_puis_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:m:p", False, False)
def c_ocr_pour_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:f:s", False, False)
def c_ocr_près_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:[me]:p", False, False)
def c_ocr_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("a") and not look(s[:m.start()], "sine +$")
def c_ocr_que_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("o") and not look(s[:m.start()], "statu +$")
def c_ocr_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:m:s", False, False)
def c_ocr_s_il_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).endswith("s")
def c_ocr_s_il_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_ocr_tard_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:ce|[mts]on|du|un|le) $")
def c_ocr_l_est_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)\w")
def c_ocr_tête_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:je|il|elle|on|ne) $")
def s_ocr_tête_1 (s, m):
    return m.group(0).replace("è", "ê").replace("È", "Ê")
def s_ocr_ton_1 (s, m):
    return m.group(0).replace("a", "o").replace("A", "O")
def s_ocr_toute_1 (s, m):
    return m.group(0).replace("n", "u").replace("N", "U")
def c_ocr_tu_es_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":(?:N.*:f:p|V0e.*:3p)", False, False)
def c_ocr_un_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:ce|d[eu]|un|quel|leur|le) +")
def c_ocr_casse1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0).istitle() and look(s[:m.start()], r"(?i)\w")
def c_ocr_casse1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(0), m.group(0)), ":G", ":M")
def s_ocr_casse1_2 (s, m):
    return m.group(0).lower()
def c_ocr_casse1_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(0), m.group(0)), ":[123][sp]", ":[MNA]|>Est ")
def s_ocr_casse1_3 (s, m):
    return m.group(0).lower()
def s_ocr_casse2_1 (s, m):
    return m.group(1).lower()
def c_ocr_casse3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)\w")
def s_ocr_casse3_1 (s, m):
    return m.group(0).lower()
def c_ocr_lettres_isolées_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("[0-9aàAÀyYdlnmtsjcçDLNMTSJCÇ_]", m.group(0)) and not look(s[:m.start()], r"\d +$") and not (m.group(0).isupper() and look(sx[m.end():], r"^\."))
def c_ocr_caractères_rares_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(0) != "<" and m.group(0) != ">"
def c_double_négation_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D:[me]" ,False, False)
def s_incohérences_globales1_1 (s, m):
    return suggSimil(m.group(2), ":[NA].*:[pi]", True)
def s_incohérences_globales2_1 (s, m):
    return suggSimil(m.group(2), ":[NA].*:[si]", True)
def c_incohérence_globale_au_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).isupper()
def c_incohérence_globale_au_qqch_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:[cdlmst]es|[nv]os|cettes?|[mts]a|mon|je|tu|ils?|elle?|[vn]ous|on|parce) ", False)
def s_incohérence_globale_au_qqch_2 (s, m):
    return suggSimil(m.group(2), ":[NA].*:[si]", True)
def c_incohérence_globale_au_qqch_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(2), m.group(2)), ">quelle ", False)
def c_incohérence_globale_au_qqch_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(2) == "combien" and morph(dDA, nextword1(s, m.end()), ":[AY]", False)
def c_incohérence_globale_aux_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).isupper()
def c_incohérence_globale_aux_qqch_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:[cdlmst]es|[nv]os|cettes?|[mts]a|mon|je|tu|ils?|elle?|[vn]ous|on|parce) ", False)
def s_incohérence_globale_aux_qqch_2 (s, m):
    return suggSimil(m.group(2), ":[NA].*:[pi]", True)
def c_incohérence_globale_aux_qqch_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(2), m.group(2)), ">quelle ", False)
def c_incohérence_globale_aux_qqch_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(2) == "combien" and morph(dDA, nextword1(s, m.end()), ":[AY]", False)
def s_incohérences_globales3_1 (s, m):
    return suggSimil(m.group(2), ":[NA].*:[pi]", True)
def c_bs_avoir_été_chez_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^avoir$", m.group(1)) and morph(dDA, (m.start(1), m.group(1)), ">avoir ", False)
def c_bs_à_date_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:être|mettre) ", False)
def c_bs_incessamment_sous_peu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1).endswith("u")
def c_bs_incessamment_sous_peu_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_bs_malgré_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look_chk1(dDA, s[m.end():], m.end(), r" \w[\w-]+ en ([aeo][a-zû]*)", ":V0a")
def c_pleo_abolir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">abolir ", False)
def c_pleo_acculer_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">acculer ", False)
def c_pleo_achever_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">achever ", False)
def c_pleo_en_cours_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], r" +de?\b")
def c_pleo_avancer_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avancer ", False)
def c_pleo_avenir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":A|>un", False)
def c_pleo_collaborer_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">collaborer ", False)
def c_pleo_comparer_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">comparer ", False)
def c_pleo_contraindre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">contraindre ", False)
def c_pleo_enchevêtrer_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">enchevêtrer ", False)
def c_pleo_entraider_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">entraider ", False)
def c_pleo_joindre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">joindre ")
def c_pleo_monter_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">monter ", False)
def c_pleo_rénover_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">rénov(?:er|ation) ", False)
def c_pleo_réunir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">réunir ", False)
def c_pleo_reculer_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">recul(?:er|) ", False)
def c_pleo_suffire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">suffire ", False)
def c_pleo_talonner_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">talonner ", False)
def c_pleo_verbe_à_l_avance_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:prévenir|prévoir|prédire|présager|préparer|pressentir|pronostiquer|avertir|devancer|deviner|réserver) ", False)
def c_pleo_différer_ajourner_reporter_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:ajourner|différer|reporter) ", False)
def c_gn_mon_ton_son_euphonie_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ">[aâeéèêiîoôuûyœæ].+:[NAQ].*:f", ":[eGW]")
def s_gn_mon_ton_son_euphonie_1 (s, m):
    return m.group(1).replace("a", "on")
def c_conf_en_mts_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":[123][sp]", ":[PY]")
def c_conf_en_mts_verbe_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(3), m.group(3)), ":3p", False)
def s_conf_en_mts_verbe_2 (s, m):
    return suggVerb(m.group(2), ":P")
def c_conf_en_mts_verbe_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (m.group(1).endswith("se ") and morph(dDA, (m.start(3), m.group(3)), ":[NA]", False))
def c_conf_malgré_le_la_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":[GNAWMB]")
def s_conf_malgré_le_la_les_1 (s, m):
    return suggSimil(m.group(1), ":[NA]", True)
def c_conf_ma_ta_cette_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]") and m.group(2)[0].islower()
def s_conf_ma_ta_cette_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:[fe]:[si]", True)
def c_conf_sa_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2)[0].islower() and morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":(?:N.*:[fe]|A|W)")
def c_conf_sa_verbe_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), "V.....[pqx]", False)
def c_conf_sa_verbe_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_conf_sa_verbe_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return hasSimil(m.group(2))
def s_conf_sa_verbe_4 (s, m):
    return suggSimil(m.group(2), ":[NA]:[fe]:[si]", True)
def c_conf_du_cet_au_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]") and m.group(2)[0].islower() and not (m.group(2) == "sortir" and re.search(r"(?i)au", m.group(1)))
def s_conf_du_cet_au_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:[me]:[si]", True)
def c_conf_ce_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]:.:[si]|:V0e.*:3[sp]|>devoir") and m.group(2)[0].islower() and hasSimil(m.group(2))
def s_conf_ce_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:[me]:[si]", True)
def c_conf_mon_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]") and m.group(2)[0].islower()
def s_conf_mon_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:.:[si]", True)
def c_conf_ton_son_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V.*:(?:Y|[123][sp])") and m.group(1)[0].islower() and look(s[:m.start()], "^ *$|, *$")
def s_conf_ton_son_verbe_1 (s, m):
    return suggSimil(m.group(1), ":[NA]:[me]:[si]", True)
def c_conf_det_plur_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]") and m.group(2)[0].islower() and not re.search(r"(?i)^quelques? soi(?:ent|t|s)\b", m.group(0))
def s_conf_det_plur_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:.:[pi]", True)
def c_conf_auxdits_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]") and m.group(2)[0].islower()
def s_conf_auxdits_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:[me]:[pi]", True)
def c_conf_auxdites_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:Y|[123][sp])", ":[NAQ]") and m.group(2)[0].islower()
def s_conf_auxdites_verbe_1 (s, m):
    return suggSimil(m.group(2), ":[NA]:[fe]:[pi]", True)
def c_conf_de_la_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":[NAQ]")
def c_conf_de_la_vconj_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V1.*:(?:Iq|Ip:2p)", ":1p")
def s_conf_de_la_vconj_2 (s, m):
    return suggVerbInfi(m.group(1))
def c_conf_de_la_vconj_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_conf_de_la_vconj_3 (s, m):
    return suggSimil(m.group(1), ":(?:[NA]:[fe]:[si])", False)
def c_conf_de_le_nom_ou_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[me]", ":[YG]") and m.group(2)[0].islower()
def c_conf_de_le_nom_ou_vconj_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[123][sp]", False)
def s_conf_de_le_nom_ou_vconj_2 (s, m):
    return suggVerbInfi(m.group(2))
def c_conf_de_l_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":[NAQ]")
def s_conf_de_l_vconj_1 (s, m):
    return suggSimil(m.group(1), ":[NA]:.:[si]", True)
def c_conf_un_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Y|[123][sp])") and not look(s[:m.start()], "(?i)(?:dont|sauf|un à) +$")
def s_conf_un_verbe_1 (s, m):
    return suggSimil(m.group(1), ":[NAQ]:[me]:[si]", True)
def c_conf_de_dès_par_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1)[0].islower() and morph(dDA, (m.start(1), m.group(1)), ":V.*:[123][sp]")
def s_conf_de_dès_par_vconj_1 (s, m):
    return suggSimil(m.group(1), ":[NA]", True)
def c_conf_d_une_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1)[0].islower() and morphex(dDA, (m.start(1), m.group(1)), ":V.*:[123][sp]", ":[GNA]") and not look(s[:m.start()], r"(?i)\b(?:plus|moins) +$")
def s_conf_d_une_vconj_1 (s, m):
    return suggSimil(m.group(1), ":[NA]", True)
def c_conf_il_on_pas_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":(?:[123][sp]|O[onw]|X)|ou ") and morphex(dDA, prevword1(s, m.start()), ":", ":3s", True)
def s_conf_il_on_pas_verbe_1 (s, m):
    return suggSimil(m.group(1), ":(?:3s|Oo)", False)
def c_conf_ils_pas_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":(?:[123][sp]|O[onw]|X)|ou ") and morphex(dDA, prevword1(s, m.start()), ":", ":3p", True)
def s_conf_ils_pas_verbe_1 (s, m):
    return suggSimil(m.group(1), ":(?:3p|Oo)", False)
def c_conf_je_pas_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":(?:[123][sp]|O[onw]|X)") and morphex(dDA, prevword1(s, m.start()), ":", ":1s", True)
def s_conf_je_pas_verbe_1 (s, m):
    return suggSimil(m.group(1), ":(?:1s|Oo)", False)
def c_conf_tu_pas_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":(?:[123][sp]|O[onw]|X)") and morphex(dDA, prevword1(s, m.start()), ":", ":(?:2s|V0e|R)", True)
def s_conf_tu_pas_verbe_1 (s, m):
    return suggSimil(m.group(1), ":(?:2s|Oo)", False)
def c_conf_adj_part_présent1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":P")
def c_conf_adj_part_présent2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]")
def c_conf_très_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:Y|[123][sp])", ":[AQW]")
def s_conf_très_verbe_1 (s, m):
    return suggSimil(m.group(1), ":[AW]", True)
def c_conf_très_verbe_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">jeûne ", False)
def s_conf_très_verbe_2 (s, m):
    return m.group(1).replace("û", "u")
def c_conf_trop_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":(?:[GNAQWM]|3p)") and not look(s[:m.start()], r"(?i)\bce que? ")
def c_conf_presque_trop_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":[GNAQWM]") and not look(s[:m.start()], r"(?i)\bce que? |ou $")
def c_conf_chez_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1)[0].isupper() and morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":[GNAQM]")
def c_conf_sur_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1)[0].isupper() and morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":[GNAQM]") and not morph(dDA, prevword1(s, m.start()), ":[NA]:[me]:si", False)
def c_conf_si_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[123][sp]", ":[GNAQWMT]") and morphex(dDA, nextword1(s, m.end()), ":", ":D", True)
def s_conf_si_vconj_1 (s, m):
    return suggSimil(m.group(1), ":[AWGT]", True)
def c_conf_de_plus_en_plus_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y)", ":(?:[GAQW]|3p)") and not morph(dDA, prevword1(s, m.start()), ":V[123].*:[123][sp]|>(?:pouvoir|vouloir|falloir) ", False, False)
def s_conf_de_plus_en_plus_verbe_1 (s, m):
    return suggVerbPpas(m.group(1))
def c_conf_a_à_grâce_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":[VN]", False, True)
def c_conf_a_à_moins_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_conf_a_à_face_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:[lmts]a|leur|une|en) +$")
def c_conf_a_à_par_rapport_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:D|Oo|M)", False)
def c_conf_a_à_être_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">être :V") and not look(s[:m.start()], r"(?i)\bce que? ")
def c_conf_a_à_l_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:côtés?|coups?|peu(?:-près|)|pics?|propos|valoir|plat-ventrismes?)", m.group(2))
def c_conf_a_à_l_à_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return re.search("(?i)^(?:côtés?|coups?|peu-près|pics?|propos|valoir|plat-ventrismes?)", m.group(2))
def c_conf_a_à_il_on_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":3s", False, False)
def c_conf_a_à_elle_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":(?:3s|R)", False, False) and not morph(dDA, nextword1(s, m.end()), ":Oo|>qui ", False, False)
def c_conf_a_à_qui_a_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":Q", ":M[12P]")
def c_conf_a_à_le_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[me]", ":(?:Y|Oo)")
def c_conf_a_à_le_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:Y|Oo)")
def c_conf_a_à_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ]", ":(?:Y|Oo)")
def c_conf_a_à_base_cause_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\bce que?\b")
def c_conf_a_à_part_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:M[12]|D|Oo)")
def c_conf_a_participe_passé_ou_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).islower() and m.group(2) != "coté"
def c_conf_a_participe_passé_ou_vconj_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:V.......[_z][az].*:Q|V1.*:Ip:2p)", ":[MGWNY]")
def c_conf_a_participe_passé_ou_vconj_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), "V1.*:(?:Ip:2p|Q)", False) and not look(s[:m.start()], r"(?i)\b(?:il +|elle +|on +|l(?:es|ui|leur) +|[nv]ous +|y +|en +|[nmtsld]’)$")
def s_conf_a_participe_passé_ou_vconj_3 (s, m):
    return suggVerbInfi(m.group(2))
def c_conf_a_participe_passé_ou_vconj_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":[123][sp]") and not m.group(2).startswith("tord")
def c_conf_a_participe_passé_ou_vconj_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V2.*:Ip:3s")
def s_conf_a_participe_passé_ou_vconj_5 (s, m):
    return suggVerbPpas(m.group(2), ":m:s")
def c_conf_a_participe_passé_ou_vconj_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_conf_a_participe_passé_ou_vconj_7 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_conf_a_à_locutions2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)[ln]’$|(?<!-)\b(?:il|elle|on|y|n’en) +$")
def c_conf_a_à_locutions3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)(?:\bque? |[ln]’$|(?<!-)\b(?:il|elle|on|y|n’en) +$)")
def c_conf_a_à_locutions4_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)(?:\bque? |[ln]’$|(?<!-)\b(?:il|elle|on|y|n’en) +$)")
def c_conf_a_à_infi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":Y", False) and not look(s[:m.start()], r"(?i)\bque? |(?:il|elle|on|n’(?:en|y)) +$")
def c_conf_mener_à_bien_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mener ", False) and ( not look(s[:m.start()], r"\bque? ") or morph(dDA, prevword1(s, m.start()), ">(?:falloir|aller|pouvoir) ", False, True) )
def c_conf_mener_à_bien_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_conf_mettre_à_profit_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mettre ", False)
def c_conf_aux_dépens_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1).endswith("x") and not m.group(1).endswith("X")
def c_conf_aux_dépens_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).endswith("ens") and not m.group(2).endswith("ENS")
def c_conf_au_temps_pour_moi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_conf_ça_sa_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not re.search("^seule?s?", m.group(2))
def c_conf_sa_ça1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":G", ">(?:tr(?:ès|op)|peu|bien|plus|moins|toute) |:[NAQ].*:f")
def c_conf_çà_ça_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\b(?:[oO]h|[aA]h) +$")
def c_conf_çà_et_là_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":R")
def c_conf_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2)[0].islower() and m.group(2) != "faire" and ( morphex(dDA, (m.start(2), m.group(2)), ":V[123].*:(?:Y|[123][sp])", ":[NAGM]|>(?:devoir|pouvoir|sembler) ") or re.search("-(?:ils?|elles?|on)$", m.group(2)) )
def c_conf_pour_ce_faire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (m.group(0).find(",") >= 0 or morphex(dDA, (m.start(2), m.group(2)), ":G", ":[AYD]"))
def c_conf_qui_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":[NAQ].*:[me]") or look(s[:m.start()], r"(?i)\b[cs]e +$")
def c_conf_ce_ne_être_doit_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:être|pouvoir|devoir) .*:3s", False)
def c_conf_ce_ne_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[123]s", ":P")
def c_conf_ce_nom1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ]", ":([123][sp]|Y|P|Q)|>l[ea]? ")
def c_conf_ce_nom2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":N.*:s", ":(?:A.*:[pi]|P|R)|>autour ")
def c_conf_c_est4_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[WX]", ":N:.*:[pi]") and morph(dDA, (m.start(3), m.group(3)), ":[RD]|>pire ", False)
def c_conf_ces_ses_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":N.*:p", ":(?:G|W|M|A.*:[si])")
def c_conf_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1).startswith("tenu") or look(s[:m.start()], "^ *$|, *$")
def c_conf_en_fin_de_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).startswith("f")
def c_conf_en_fin_de_compte_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).startswith("l")
def c_régler_son_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">régler ", False)
def c_conf_date1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "(?i)^ +(?:fra[iî]ches|dénoyautées|fourrées|sèches|séchées|cultivées|produites|muscade|medjool|Hamraya|deglet[ -]nour|kenta|allig|khouat)") or look(s[:m.start()], r"(?i)\b(?:confiture|crème|gâteau|mélasse|noyau|pâte|recette|sirop)[sx]? de +$|\b(?:moelleux|gateau|fondant|cake)[sx]? aux +$")
def c_conf_dans1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("en") or look(s[:m.start()], "^ *$")
def c_conf_être_davantage_ppas_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False) and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ]", ":G")
def c_conf_davantage1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":Q")
def c_conf_davantage2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ">(?:profiter|bénéficier) ", False)
def c_conf_différent_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":W", False, False)
def s_conf_différent_1 (s, m):
    return m.group(0).replace("end", "ent")
def c_conf_différend1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, nextword1(s, m.end()), ":[GVX]", ":[NAQ]", True)
def c_conf_différend2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, nextword1(s, m.end()), ":[GVX]", ":[NAQ]", True) and not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def c_conf_un_différend_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, nextword1(s, m.end()), ":[GV]", ":[NAQ]", False)
def c_conf_différends_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, nextword1(s, m.end()), ":[GV]", ":[NAQ]", True)
def c_conf_les_différends_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, nextword1(s, m.end()), ":G", ":[NAQ]", False)
def c_conf_être_différent_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def s_conf_être_différent_1 (s, m):
    return m.group(2).replace("nd", "nt")
def c_conf_eh_bien_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and not morph(dDA, nextword1(s, m.end()), ":[WAY]", False, False)
def c_conf_eh_ben_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1).startswith("B")
def c_conf_faux_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ">(?:ils?|ne|en|y|leur|lui|nous|vous|[mtsl]e|la|les) ", False, True) and morphex(dDA, nextword1(s, m.end()), ":",  ":(?:Y|Oo|X|M)", True)
def s_conf_flan_1 (s, m):
    return m.group(1).replace("c", "").replace("C", "")
def s_conf_flanc_1 (s, m):
    return m.group(0).replace("an", "anc").replace("AN", "ANC")
def c_conf_sur_le_flanc_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:attaquer|allonger|blesser|coucher|étendre|toucher) ", False)
def s_conf_sur_le_flanc_1 (s, m):
    return m.group(0).replace("an", "anc").replace("AN", "ANC")
def c_conf_tirer_au_flanc_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tir(?:er|) ", False)
def s_conf_tirer_au_flanc_1 (s, m):
    return m.group(0).replace("an", "anc").replace("AN", "ANC")
def c_conf_la_là_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":E|>le ", False, False)
def c_conf_les1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":N.*:m:[pi]")
def c_conf_les2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "^ *$|^,") or morph(dDA, prevword1(s, m.start()), ":D.*:p")
def c_conf_les2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_conf_leurs_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|Y)", ":(?:G|N|A|M[12P])") and not look(s[:m.start()], r"(?i)\b[ld]es +$")
def c_conf_loin_s_en_faut_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)loin s’en faut", m.group(0)) and morph(dDA, prevword1(s, m.start()), ":N", ">(?:aller|venir|partir) ", True)
def c_mais_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":O", ":3s") and look(s[:m.start()], "^ *$|, *$")
def c_conf_on_ont_adverbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":W", ":3s") and not morph(dDA, prevword1(s, m.start()), ":V.*:3s", False, False)
def c_conf_où_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":3[sp]", ":Y")
def c_conf_vers_où_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def s_conf_pale_pâle1_1 (s, m):
    return m.group(1).replace("pal", "pâl")
def s_conf_pale_pâle2_1 (s, m):
    return m.group(1).replace("pal", "pâl")
def c_conf_peut_adv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "très +$")
def c_conf_cela_peut_être_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[AQ]", False)
def c_conf_peu_importe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":C", False, True)
def c_conf_un_peu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "(?i)(?:quelqu|l|d)’")
def c_conf_peu_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A") and not re.search("(?i)^seule?s?$", m.group(2)) and not look(s[:m.start()], r"(?i)\b(?:il|on|ne|je|tu) +$")
def c_conf_par_dessus_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":D|>bord ", False) and not morph(dDA, prevword1(s, m.start()), ":D.*:[me]|>(?:grande|petite) ", False, False)
def c_conf_prêt_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "(?i)(?:peu|de|au plus) $") and morph(dDA, (m.start(2), m.group(2)), ":Y|>(?:tout|les?|la) ")
def c_conf_près_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:Y|M[12P])|>(?:en|y|les?) ", False)
def c_conf_quant_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ">(?:arriver|venir|à|revenir|partir|aller) ") and not(m.group(0).endswith("à") and look(s[m.end():], "^ +[mts]on tour[, ]"))
def c_conf_qu_en2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":P", False)
def c_conf_quand2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], "^ +ne s(?:ai[st]|u[st]|urent|avai(?:[ts]|ent)) ")
def c_conf_quand_bien_même_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], "^ si ")
def c_conf_quelle_nom_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ]", ":(?:G|[123][sp]|W)")
def s_conf_quelle_nom_adj_1 (s, m):
    return m.group(1).replace(" ", "")
def c_conf_qu_elle_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).islower() and (morphex(dDA, (m.start(2), m.group(2)), ":V|>(?:ne?|me?|te?|se?|[nv]ous|l(?:e|a|es|ui|leur|)|en|y) ", ":[NA].*:[fe]") or m.group(2) == "t" or m.group(2) == "s")
def c_conf_qu_elle_verbe_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("e") and not morph(dDA, (m.start(2), m.group(2)), ":V0e", False)
def c_conf_qu_elle_verbe_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(1).endswith("s") and not morph(dDA, (m.start(2), m.group(2)), ":V0e", False)
def c_conf_qu_elle_verbe_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":V0e", False) and morphex(dDA, nextword1(s, m.end()), ":[QA]", ":G", False)
def c_conf_qu_elle_verbe_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("e")
def c_conf_qu_elle_verbe_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(1).endswith("s")
def c_être_pas_sans_savoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def c_conf_il_on_s_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and morph(dDA, (m.start(2), m.group(2)), ":V", False)
def c_conf_elle_s_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and morph(dDA, (m.start(2), m.group(2)), ":V", False) and not ( m.group(1) == "sans" and morph(dDA, (m.start(2), m.group(2)), ":[NY]", False) )
def c_conf_son_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NA].*:[me]:s|>[aeéiîou].* :[NA].*:f:s", ":[GW]") and morphex(dDA, prevword1(s, m.start()), ":V|>(?:à|avec|chez|dès|contre|devant|derrière|en|par|pour|sans|sur) ", ":[NA].*:[pi]|>(?:ils|elles|vous|nous|leur|lui|[nmts]e) ", True) and not look(s[:m.start()], r"(?i)\bce que? |[mts]’en +$")
def c_conf_qui_sont_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, nextword1(s, m.end()), ":[DR]", False, True)
def c_conf_sûr_de_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":M[12]", False)
def c_conf_en_temps_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], "^[ ’](?:lieux|endroits|places|mondes|villes|pays|régions|cités)")
def c_conf_ouvrir_la_voix_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">ouvrir ", False)
def c_conf_voir_voire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^(?:grand|petit|rouge)$", m.group(2)) and morphex(dDA, (m.start(2), m.group(2)), ":A", ":[NGM]") and not m.group(2).istitle() and not look(s[:m.start()], r"(?i)\b[ndmts](?:e |’(?:en |y ))(?:pas |jamais |) *$") and not morph(dDA, prevword1(s, m.start()), ":O[os]|>(?:[ndmts]e|falloir|pouvoir|savoir|de) ", False)
def c_conf_voire_voir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":Cs|>(?:ni|et|sans|pour|falloir|[pv]ouvoir|aller) ", True, False)
def c_conf_j_y_en_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|O[onw])")
def s_conf_j_y_en_qqch_1 (s, m):
    return suggSimil(m.group(2), ":1s", False)
def c_conf_ne_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P|O[onw]|X)|>(?:[lmtsn]|surtout|guère|presque|même|tout|parfois|vraiment|réellement) ") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_ne_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Oo|Y)", False)
def c_conf_n_y_en_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P|O[onw]|X)") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_n_y_en_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Y)", False)
def c_conf_ne_pronom_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P|O[onw]|X)") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_ne_pronom_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Y)", False)
def c_conf_me_te_se_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^se que?", m.group(0)) and morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P|Oo)|>[lmts] ") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_me_te_se_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Oo|Y)", False)
def c_conf_m_t_s_y_en_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P|X|Oo)|rien ") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_m_t_s_y_en_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Y)", False)
def c_conf_m_s_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P)|>(?:en|y|ils?) ") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_m_s_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Y)", False)
def c_conf_t_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":(?:[123][sp]|Y|P)|>(?:en|y|ils?|elles?) ") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|ce)$", m.group(2))
def s_conf_t_qqch_1 (s, m):
    return suggSimil(m.group(2), ":(?:[123][sp]|Y)", False)
def c_conf_c_ç_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":", ":[123][sp]|>(?:en|y|que?) ") and not re.search("(?i)-(?:ils?|elles?|[nv]ous|je|tu|on|dire)$", m.group(2))
def s_conf_c_ç_qqch_1 (s, m):
    return suggSimil(m.group(2), ":3s", False)
def c_conj_xxxai_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( morph(dDA, (m.start(0), m.group(0)), ":1s") or ( look(s[:m.start()], "> +$") and morph(dDA, (m.start(0), m.group(0)), ":1s", False) ) ) and not (m.group(0)[0:1].isupper() and look(sx[:m.start()], r"\w")) and not look(s[:m.start()], r"(?i)\b(?:j(?:e |[’'])|moi(?:,? qui| seul) )")
def s_conj_xxxai_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3s")
def c_conj_xxxes_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(0), m.group(0)), ":2s", ":(?:E|G|W|M|J|[13][sp]|2p)") and not m.group(0)[0:1].isupper() and not look(s[:m.start()], "^ *$") and ( not morph(dDA, (m.start(0), m.group(0)), ":[NAQ]", False) or look(s[:m.start()], "> +$") ) and not look(s[:m.start()], r"(?i)\bt(?:u |[’']|oi,? qui |oi seul )")
def s_conj_xxxes_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3s")
def c_conj_xxxas_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(0), m.group(0)), ":2s", ":(?:G|W|M|J|[13][sp]|2p)") and not (m.group(0)[0:1].isupper() and look(sx[:m.start()], r"\w")) and ( not morph(dDA, (m.start(0), m.group(0)), ":[NAQ]", False) or look(s[:m.start()], "> +$") ) and not look(s[:m.start()], r"(?i)\bt(?:u |[’']|oi,? qui |oi seul )")
def s_conj_xxxas_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3s")
def c_conj_xxxxs_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(0), m.group(0)), ":[12]s", ":(?:E|G|W|M|J|3[sp]|2p|1p)") and not (m.group(0)[0:1].isupper() and look(sx[:m.start()], r"\w")) and ( not morph(dDA, (m.start(0), m.group(0)), ":[NAQ]", False) or look(s[:m.start()], "> +$") or ( re.search("(?i)^étais$", m.group(0)) and not morph(dDA, prevword1(s, m.start()), ":[DA].*:p", False, True) ) ) and not look(s[:m.start()], r"(?i)\b(?:j(?:e |[’'])|moi(?:,? qui| seul) |t(?:u |[’']|oi,? qui |oi seul ))")
def s_conj_xxxxs_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3s")
def c_conj_peux_veux_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (m.group(0)[0:1].isupper() and look(sx[:m.start()], r"\w")) and not look(s[:m.start()], r"(?i)\b(?:j(?:e |[’'])|moi(?:,? qui| seul) |t(?:u |[’']|oi,? qui |oi seul ))")
def s_conj_peux_veux_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3s")
def c_conj_équivaux_prévaux_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (m.group(0)[0:1].isupper() and look(sx[:m.start()], r"\w")) and not (m.group(0) == "vaux" and morph(dDA, prevword1(s, m.start()), ":(?:R|D.*:p)", False, False)) and not look(s[:m.start()], r"(?i)\b(?:j(?:e |[’'])|moi(?:,? qui| seul) |t(?:u |[’']|oi,? qui |oi seul ))")
def s_conj_équivaux_prévaux_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3s")
def c_conj_xxxons_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(0), m.group(0)), ":V.*:1p", ":[EGMNAJ]") and not (m.group(0)[0:1].isupper() and look(s[:m.start()], r"\w")) and not look(sx[:m.start()], r"\b(?:[nN]ous(?:-mêmes?|)|[eE]t moi(?:-même|)|[nN]i (?:moi|nous)),? ")
def s_conj_xxxons_sans_sujet_1 (s, m):
    return suggVerb(m.group(0), ":3p")
def c_conj_xxxez_sans_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(0), m.group(0)), ":V.*:2p", ":[EGMNAJ]") and not (m.group(0)[0:1].isupper() and look(s[:m.start()], r"\w")) and not look(sx[:m.start()], r"\b(?:[vV]ous(?:-mêmes?|)|[eE]t toi(?:-même|)|[tT]oi(?:-même|) et|[nN]i (?:vous|toi)),? ")
def c_p_tout_débuts_petits_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"\b(aux|[ldmtsc]es|[nv]os|leurs) +$")
def c_p_les_tout_xxx_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[AQ].*:[pi]", False)
def c_gn_tous_deux_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_gn_tous_déterminant_pluriel_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:d[eu]|avant|après|sur|malgré) +$")
def c_gn_tous_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:d[eu]|avant|après|sur|malgré) +$") and not morph(dDA, (m.start(2), m.group(2)), ":(?:3s|Oo)", False)
def c_gn_tous_ceux_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:d[eu]|avant|après|sur|malgré) +$")
def c_gn_toutes_déterminant_nom_fem_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":f", ":(?:[123][sp]|[me])") and morphex(dDA, prevword1(s, m.start()), ":", ":(?:R|[123][sp]|Q)|>(?:[nv]ous|eux) ", True)
def c_gn_toutes_déterminant_nom_fem_plur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_toutes_déterminant_nom_fem_plur_2 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_tous_déterminant_nom_mas_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":m", ":(?:[123][sp]|[fe])") and morphex(dDA, prevword1(s, m.start()), ":", ":(?:R|[123][sp]|Q)|>(?:[nv]ous|eux) ", True)
def c_gn_tous_déterminant_nom_mas_plur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_tous_déterminant_nom_mas_plur_2 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_tout_nom_mas_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":N.*:[fp]", ":(?:A|W|G|M[12P]|Y|[me]:i|3s)") and morph(dDA, prevword1(s, m.start()), ":R|>de ", False, True)
def s_gn_tout_nom_mas_sing_1 (s, m):
    return suggMasSing(m.group(1), True)
def c_gn_toute_nom_fem_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[mp]") and morph(dDA, prevword1(s, m.start()), ":R|>de ", False, True)
def s_gn_toute_nom_fem_sing_1 (s, m):
    return suggFemSing(m.group(1), True)
def c_gn_tous_nom_mas_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fs]") and morph(dDA, prevword1(s, m.start()), ":R|>de ", False, True)
def s_gn_tous_nom_mas_plur_1 (s, m):
    return suggMasPlur(m.group(1), True)
def c_gn_toutes_nom_fem_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[ms]") and morph(dDA, prevword1(s, m.start()), ":R|>de ", False, True)
def s_gn_toutes_nom_fem_plur_1 (s, m):
    return suggFemPlur(m.group(1), True)
def c_ne_manquant1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[123][sp]", False) and not (re.search("(?i)^(?:jamais|rien)$", m.group(2)) and look(s[:m.start()], r"\b(?:que?|plus|moins) "))
def c_ne_manquant2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[123][sp]", False) and not (re.search("(?i)^(?:jamais|rien)$", m.group(2)) and look(s[:m.start()], r"\b(?:que?|plus|moins) "))
def c_ne_manquant3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[123][sp]", False) and not (re.search("(?i)^(?:jamais|rien)$", m.group(3)) and look(s[:m.start()], r"\b(?:que?|plus|moins) "))
def c_ne_manquant4_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[123][sp]", False) and not (re.search("(?i)^(?:jamais|rien)$", m.group(3)) and look(s[:m.start()], r"\b(?:que?|plus|moins) "))
def c_infi_ne_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":(?:Y|W|O[ow])|>que? ", False) and _oSpellChecker.isValid(m.group(1))
def s_infi_ne_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_imp_infinitif_erroné_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V1.*:Y", False) and look(s[:m.start()], "^ *$|, *$")
def s_imp_infinitif_erroné_1 (s, m):
    return suggVerbTense(m.group(1), ":E", ":2p")
def c_p_en_année_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":[AN].*:[pi]", False, False)
def c_p_de_année_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A.*:s", False)
def c_p_un_nombre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A.*:s")
def c_loc_côte_à_côte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^côte à côte$", m.group(0))
def c_p_grand_bien_lui_fasse_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def p_p_le_pour_et_le_contre_1 (s, m):
    return m.group(0).replace(" ", "_")
def c_loc_tour_à_tour_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^tour à tour$", m.group(0))
def c_p_qqch_tiret_là_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":G")
def c_p_tout_au_long_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def c_p_suite_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:une|la|cette|[mts]a|[nv]otre|de) +")
def c_p_dét_plur_nombre_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NA].*:[pi]", ":(?:V0|3p)|>(?:janvier|février|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|décembre|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor)")
def c_loc_arc_à_poulies_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_armes_à_feu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_bombe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_canne_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).find("ane") != -1
def s_loc_canne_à_1 (s, m):
    return m.group(1).replace("ane", "anne")
def c_loc_canne_à_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(3) == "a"
def c_loc_caisse_à_outils_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_chair_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_crayon_à_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_cuillère_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_fard_à_paupières_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_fils_fille_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_gaz_à_effet_de_serre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_lime_à_ongles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_machine_à_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_p_mineur_de_moins_de_x_ans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).isdigit() or morph(dDA, (m.start(2), m.group(2)), ":B", False)
def c_loc_moule_à_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_p_numéro_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"\b[lL]a +$")
def d_p_numéro_1 (s, m, dDA):
    return define(dDA, m.start(0), [">numéro :N:f:s"])
def c_p_papier_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_remire_à_plat_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_rouge_à_lèvres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_sac_à_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_silo_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_soue_à_cochons_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_p_trou_à_rat_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_tueur_à_gages_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_vente_à_domicile_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_vernis_à_ongles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_vol_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_loc_voie_de_recours_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("x")
def c_loc_usine_à_gaz_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "a"
def c_p_qqch_100_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", ":(?:G|3p)")
def c_p_det_plur_nombre_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", ":(?:G|3p)")
def c_p_à_xxx_pour_cent_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":B", False)
def c_p_au_moins_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":[AQ].*:[me]:[si]", False)
def c_p_au_hasard_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return isEndOfNG(dDA, s[m.end():], m.end())
def c_p_aussi_adv_que_possible_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":W", False)
def c_p_au_sens_adj_du_terme_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":A .*:m:s", False)
def c_p_nombre_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":(?:R|C[sc])", False, True)
def c_p_à_xxx_reprises_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":B", False) or re.search("(?i)^(?:plusieurs|maintes)", m.group(1))
def c_p_bien_entendu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, nextword1(s, m.end()), ":[NAQR]|>que? ", False, True)
def c_p_comme_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":V0")
def c_p_pêle_mêle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_p_droit_devant_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":D.*:[me]:[si]", False)
def c_p_dans_xxx_cas_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":([AQ].*:[me]:[pi])", False, False)
def c_p_du_coup_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A", False)
def c_p_verbe_pronom_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:croire|devoir|estimer|imaginer|penser) ")
def c_p_en_partie_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:R|D|[123]s|X)", False)
def c_p_en_plus_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, nextword1(s, m.end()), ":A", False, True)
def c_p_en_plus_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_p_en_quelques_tps1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":[AQ]:[ef]:[si]", False)
def c_p_en_quelques_tps2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":[AQ]:[em]:[si]", False)
def c_p_entre_pronom_et_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:il +|n’)$")
def c_p_haut_et_fort_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def c_p_hélas_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\bt(?:u|oi qui)[ ,]")
def c_p_nécessité_fait_loi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def c_p_non_par_trop_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A", False)
def c_p_plein_est_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def c_p_plus_adv_que_prévu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":W", False)
def c_p_plus_adv_que_les_autres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[AW]", ":G")
def c_p_plus_adv_les_uns_que_les_autres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[AW]", False)
def c_p_pour_autant_que_su_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":Y", False)
def c_p_tambour_battant_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":(?:V|N:f)", ":G")
def c_p_tête_baissée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NV]", ":D")
def c_p_tant_que_ça_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":(?:3s|X)", False)
def c_p_putain_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[me]", False)
def c_p_nom_propre_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M[12]", False)
def c_p_nom_propre_nom_propre_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and m.group(2) != ""
def c_p_de_nom_propre_et_ou_de_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M", False) and morph(dDA, (m.start(2), m.group(2)), ":M", False)
def c_p_de_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M", False) or not _oSpellChecker.isValid(m.group(1))
def c_p_entre_nom_propre_et_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:M[12]|N)") and morph(dDA, (m.start(2), m.group(2)), ":(?:M[12]|N)")
def c_p_en_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":MP")
def c_p_titre_masculin_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M[12]", False)
def c_p_titre_féminin_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M[12]", False)
def c_p_nom_propre_et_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[MT]", False) and morph(dDA, prevword1(s, m.start()), ":Cs", False, True) and not look(s[:m.start()], r"\b(?:plus|moins|aussi) .* que +$")
def p_p_nom_propre_et_pronom_1 (s, m):
    return rewriteSubject(m.group(1),m.group(2))
def c_p_être_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def c_p_être_pronom_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def c_p_qqch_on_ne_peut_plus_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:V0e|N)", False) and morph(dDA, (m.start(3), m.group(3)), ":[AQ]", False)
def c_p_avoir_être_loc_adv1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0", False)
def c_p_avoir_être_loc_adv2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0", False) and morph(dDA, (m.start(3), m.group(3)), ":[QY]", False)
def c_p_avoir_loc_adv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and not (m.group(2) == "crainte" and look(s[:m.start()], r"\w"))
def c_p_avoir_pronom_loc_adv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_p_avoir_tous_toutes_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morph(dDA, (m.start(3), m.group(3)), ":B", False) and morph(dDA, (m.start(4), m.group(4)), ">besoin |:(?:Q|V1.*:Y)", False)
def c_p_elle_aussi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A:[fe]:s", False)
def c_p_elle_aussi_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(2), m.group(2)), ":W", ":3s") and morph(dDA, nextword1(s, m.end()), ":A:[fe]:s", False, True)
def c_p_elles_aussi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A:[fe]:p", False)
def c_p_elles_aussi_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(2), m.group(2)), ":W", ":3p") and morph(dDA, nextword1(s, m.end()), ":A:[fe]:p", False, True)
def c_p_verbe_loc_adv1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False)
def c_p_verbe_loc_adv2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V[123]")
def c_p_verbe_loc_adv3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V[123]", False)
def c_p_verbe_pronom_aussi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False)
def c_p_verbe_même_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":G")
def c_p_le_xxx_le_plus_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":G") and morph(dDA, (m.start(3), m.group(3)), ":[AQ].*:[me]", False)
def c_p_la_xxx_la_plus_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":G") and morph(dDA, (m.start(3), m.group(3)), ":[AQ].*:[fe]", False)
def c_p_les_xxx_les_plus_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", ":[123][sp]") and morph(dDA, (m.start(3), m.group(3)), ":A.*:[pi]", False)
def c_p_le_plus_le_moins_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A", ":([me]:[si]|G)") and morph(dDA, prevword1(s, m.start()), ">(?:avoir|être) :V", False)
def c_p_bien_mal_fort_adj_adv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[AW]")
def c_p_loc_adj_adv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[AW]", False)
def c_p_un_brin_chouïa_rien_tantinet_soupçon_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":A", ":G")
def c_p_assez_trop_adv_xxxment_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":W", ":3p")
def c_p_assez_trop_adj_adv_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[AW]", ":[123][sp]")
def c_p_le_la_plus_moins_adv_xxxment_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False) and morph(dDA, (m.start(3), m.group(3)), ":W", False) and morph(dDA, (m.start(4), m.group(4)), ":[AQ]", False)
def c_p_complètement_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, True)
def c_p_adverbe_xxxment_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":W\\b")
def c_p_couleurs_invariables_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False)
def c_p_locutions_adj_nom_et_couleurs_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:N|A|Q|V0e)", ":D")
def c_p_jamais1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\bne +$")
def c_p_à_nos_yeux_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[pi]", False)
def c_p_à_la_dernière_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[si]", False)
def c_p_à_l_époque_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[si]", False)
def c_p_au_pire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":A", ":N:[me]:[si]")
def c_p_ben_voyons_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_p_chaque_année_semaine_journée_décennie_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":(?:A.*:[fe]:[si]|Oo|[123][sp])", False)
def c_p_chaque_an_jour_mois_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":(?:A.*:[me]:[si]|Oo|[123][sp])", False)
def c_p_d_évidence_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[si]", False)
def c_p_dans_l_ensemble_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[si]", False)
def c_p_de_ce_seul_fait_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[si]", False)
def c_p_dès_le_départ_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[si]")
def c_p_dès_les_premiers_jours_mois_ans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[pi]", False)
def c_p_dès_les_premières_années_heures_minutes_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[pi]", False)
def c_p_en_certaines_plusieurs_occasions_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[pi]", False)
def c_p_entre_autres_choses_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[pi]", False)
def c_p_quelques_minutes_heures_années_plus_tard_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[fe]:[pi]", False)
def c_p_quelques_instants_jours_siècles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[pi]", False)
def c_p_un_moment_instant_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":A.*:[me]:[si]", False)
def c_loc_arriver_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">arriver ", False)
def c_loc_arriver_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(3) == "a"
def c_p_donner_sens_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:re|)donner ", False)
def c_p_faire_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False)
def c_p_faire_qqch_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_loc_laisser_pour_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">laisser ", False)
def c_loc_laisser_pour_compte_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "compte"
def c_loc_mettre_à_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mettre ", False)
def c_loc_mettre_à_qqch_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(3) == "a"
def c_p_mettre_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mettre ", False)
def c_loc_mourir_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mourir ", False)
def s_loc_mourir_qqch_1 (s, m):
    return m.group(2).replace("û", "u")
def c_p_paraitre_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">para[îi]tre ", False)
def s_p_paraitre_qqch_1 (s, m):
    return m.group(2).replace("û", "u")
def c_p_porter_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">porter ", False)
def c_loc_prendre_à_la_légère_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">prendre ", False)
def c_loc_prendre_à_la_légère_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(3) == "a"
def c_p_prendre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">prendre ", False)
def c_loc_rendre_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">rendre ", False)
def c_loc_rester_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">rester ", False)
def c_loc_rester_qqch_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">jeûne ", False)
def s_loc_rester_qqch_2 (s, m):
    return m.group(2).replace("û", "u")
def c_loc_rester_qqch_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_loc_semble_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">sembler ", False)
def s_loc_semble_qqch_1 (s, m):
    return m.group(2).replace("û", "u")
def c_p_sembler_paraitre_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:sembler|para[îi]tre) ") and morphex(dDA, (m.start(3), m.group(3)), ":A", ":G")
def c_loc_suivre_de_près_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">suivre ", False)
def c_loc_suivre_de_près_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(3) != "près"
def c_loc_tenir_à_distance_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tenir ", False)
def c_loc_tenir_à_distance_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(3) == "a"
def c_loc_tenir_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tenir ", False)
def c_loc_tenir_compte_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">co[mn]te(?:sse|) ", False)
def c_p_tirer_profit_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tirer ", False)
def c_loc_tourner_court_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tourner ", False)
def c_loc_tourner_court_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "court"
def c_p_trier_sur_le_volet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">trier ", False)
def c_p_venir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">venir ", False)
def c_redondances_phrase_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":(?:G|V0)|>même ", False)
def c_redondances_phrase_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_au_le_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ]", False)
def c_au_les_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ]", False)
def c_au_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[fe]", False)
def c_gn_l_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p", ":[123][sp]|:[si]")
def s_gn_l_accord_1 (s, m):
    return suggSing(m.group(1))
def c_gn_le_accord1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:e|m|P|G|W|[123][sp]|Y)")
def s_gn_le_accord1_1 (s, m):
    return suggLesLa(m.group(2))
def c_gn_le_accord1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_le_accord1_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_le_accord1_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")
def s_gn_le_accord1_3 (s, m):
    return suggMasSing(m.group(2))
def c_gn_le_accord1_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_gn_le_accord2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":D", False)
def c_gn_le_accord2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f", ":(?:e|m|P|G|W|[123][sp]|Y)") or ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f", ":[me]") and morphex(dDA, (m.start(1), m.group(1)), ":R", ">(?:e[tn]|ou) ") and not (morph(dDA, (m.start(1), m.group(1)), ":Rv", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False)) )
def s_gn_le_accord2_2 (s, m):
    return suggLesLa(m.group(3))
def c_gn_le_accord2_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(3))
def s_gn_le_accord2_3 (s, m):
    return suggMasSing(m.group(3), True)
def c_gn_le_accord2_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p") or ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[si]") and morphex(dDA, (m.start(1), m.group(1)), ":[RC]", ">(?:e[tn]|ou)") and not (morph(dDA, (m.start(1), m.group(1)), ":Rv", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False)) )
def s_gn_le_accord2_4 (s, m):
    return suggMasSing(m.group(3))
def c_gn_le_accord2_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_gn_le_accord3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:e|m|P|G|W|Y)")
def s_gn_le_accord3_1 (s, m):
    return suggLesLa(m.group(2))
def c_gn_le_accord3_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_le_accord3_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_le_accord3_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_le_accord3_3 (s, m):
    return suggMasSing(m.group(2))
def c_gn_le_accord3_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_gn_ledit_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":[GWme]")
def c_gn_ledit_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_ledit_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_ledit_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_ledit_accord_3 (s, m):
    return suggMasSing(m.group(2))
def c_gn_un_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:e|m|G|W|V0|3s|Y)")
def c_gn_un_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_un_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_un_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]") and not morph(dDA, prevword(s, m.start(), 2), ":B", False)
def s_gn_un_accord_3 (s, m):
    return suggMasSing(m.group(2))
def c_gn_un_des_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:e|m|G|W|V0|3s)")
def c_gn_un_des_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_un_des_accord_2 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_du_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":[GWme]")
def c_gn_du_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_du_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_du_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_du_accord_3 (s, m):
    return suggMasSing(m.group(2))
def c_gn_cet_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":[GWme]")
def c_gn_cet_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_cet_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_cet_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ">[bcçdfgjklmnpqrstvwxz].+:[NAQ].*:m", ":[efGW]")
def c_gn_cet_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_cet_accord_4 (s, m):
    return suggMasSing(m.group(2))
def c_gn_ce_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:3s|[GWme])")
def c_gn_ce_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_ce_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_ce_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":[GWme]") and morph(dDA, (m.start(2), m.group(2)), ":3s", False)
def c_gn_ce_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_ce_accord_4 (s, m):
    return suggMasSing(m.group(2))
def c_gn_mon_ton_son_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_mon_ton_son_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ">[bcdfgjklmnpqrstvwxz].*:[NAQ].*:f", ":[GWme]")
def s_gn_mon_ton_son_accord_2 (s, m):
    return m.group(1).replace("on", "a")
def c_gn_mon_ton_son_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_mon_ton_son_accord_3 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_mon_ton_son_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_mon_ton_son_accord_4 (s, m):
    return suggMasSing(m.group(2))
def c_gn_au_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:s", ":[GWme]")
def c_gn_au_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_au_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_au_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_au_accord_3 (s, m):
    return suggMasSing(m.group(2))
def c_gn_au_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_gn_la_accord1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:e|f|P|G|W|[1-3][sp]|Y)")
def c_gn_la_accord1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_la_accord1_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_la_accord1_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")
def s_gn_la_accord1_3 (s, m):
    return suggFemSing(m.group(2))
def c_gn_la_accord2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":D", False)
def c_gn_la_accord2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":(?:e|f|P|G|W|[1-3][sp]|Y)") or ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":[fe]") and morphex(dDA, (m.start(1), m.group(1)), ":[RC]", ">(?:e[tn]|ou) ") and not (morph(dDA, (m.start(1), m.group(1)), ":(?:Rv|C)", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False)) )
def c_gn_la_accord2_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(3))
def s_gn_la_accord2_3 (s, m):
    return suggFemSing(m.group(3), True)
def c_gn_la_accord2_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p") or ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[si]") and morphex(dDA, (m.start(1), m.group(1)), ":[RC]", ">(?:e[tn]|ou)") and not (morph(dDA, (m.start(1), m.group(1)), ":Rv", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False)) )
def s_gn_la_accord2_4 (s, m):
    return suggFemSing(m.group(3))
def c_gn_la_accord3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":[efPGWY]")
def c_gn_la_accord3_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_la_accord3_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_la_accord3_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_la_accord3_3 (s, m):
    return suggFemSing(m.group(2))
def c_gn_ladite_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":[efGW]")
def c_gn_ladite_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_ladite_accord_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_ladite_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_ladite_accord_3 (s, m):
    return suggFemSing(m.group(2))
def c_gn_une_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:e|f|G|W|V0|3s|P)") and not ( m.group(2) == "demi" and morph(dDA, nextword1(s, m.end()), ":N.*:f") )
def c_gn_une_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_une_accord_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_une_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]") and not morph(dDA, prevword(s, m.start(), 2), ":B", False)
def s_gn_une_accord_3 (s, m):
    return suggFemSing(m.group(2))
def c_gn_une_des_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:e|f|G|W|V0|3s)")
def c_gn_une_des_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_une_des_accord_2 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_cette_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":[efGW]")
def s_gn_cette_accord_1 (s, m):
    return suggCeOrCet(m.group(2))
def c_gn_cette_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_cette_accord_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_cette_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_cette_accord_3 (s, m):
    return suggFemSing(m.group(2))
def c_gn_ma_ta_sa_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":[efGW]")
def s_gn_ma_ta_sa_accord_1 (s, m):
    return m.group(1).replace("a", "on")
def c_gn_ma_ta_sa_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and not re.search("(?i)^[aâeéèêiîoôuûyœæ]", m.group(2)) and hasFemForm(m.group(2))
def s_gn_ma_ta_sa_accord_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_ma_ta_sa_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def s_gn_ma_ta_sa_accord_3 (s, m):
    return suggFemSing(m.group(2))
def c_gn_certains_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":[emGWP]")
def c_gn_certains_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_certains_accord_2 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_certains_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":(?:[ipGWP]|V0)") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(1) in aREGULARPLURAL
def s_gn_certains_accord_3 (s, m):
    return suggPlur(m.group(2))
def c_gn_certains_des_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":[emGW]")
def c_gn_certains_des_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasMasForm(m.group(2))
def s_gn_certains_des_accord_2 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_certaines_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":[efGWP]")
def c_gn_certaines_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_certaines_accord_2 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_certaines_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[ipGWP]") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(2) in aREGULARPLURAL
def s_gn_certaines_accord_3 (s, m):
    return suggPlur(m.group(2))
def c_gn_certaines_des_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":[efGW]")
def c_gn_certaines_des_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_certaines_des_accord_2 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_leur_accord1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")
def c_gn_leur_accord1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_leur_accord1_2 (s, m):
    return suggSing(m.group(2))
def c_gn_leur_accord2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p") or ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[si]") and morphex(dDA, (m.start(1), m.group(1)), ":[RC]|>de ", ">(?:e[tn]|ou)") and not (morph(dDA, (m.start(1), m.group(1)), ":Rv", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False)) )
def c_gn_leur_accord2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_leur_accord2_2 (s, m):
    return suggSing(m.group(3))
def c_gn_leur_accord3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siGW]")
def c_gn_leur_accord3_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_leur_accord3_2 (s, m):
    return suggSing(m.group(2))
def c_gn_notre_votre_chaque_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p", ":[siGW]")
def s_gn_notre_votre_chaque_accord_1 (s, m):
    return suggSing(m.group(1))
def c_gn_quelque_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[siG]")
def c_gn_les_accord1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False)) ) or m.group(2) in aREGULARPLURAL
def s_gn_les_accord1_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_les_accord2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":D", False)
def c_gn_les_accord2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s") or (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[pi]|>avoir") and morphex(dDA, (m.start(1), m.group(1)), ":[RC]", ">(?:e[tn]|ou) ") and not (morph(dDA, (m.start(1), m.group(1)), ":Rv", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False))) ) and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))
def s_gn_les_accord2_2 (s, m):
    return suggPlur(m.group(3))
def c_gn_les_accord3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[ipYPGW]") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(2) in aREGULARPLURAL
def s_gn_les_accord3_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_leurs_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":(?:[ipGW]|[123][sp])") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(2) in aREGULARPLURAL
def s_gn_leurs_accord_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_leurs_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_gn_det_pluriel_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":[ipGW]") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(1) in aREGULARPLURAL
def s_gn_det_pluriel_accord_1 (s, m):
    return suggPlur(m.group(1))
def c_gn_ces_aux_pluriel_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[ipGW]") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(2) in aREGULARPLURAL
def s_gn_ces_aux_pluriel_accord_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_ces_aux_pluriel_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morphex(dDA, (m.start(2), m.group(2)), ">[bcdfglklmnpqrstvwxz].*:m", ":f")
def c_gn_ces_aux_pluriel_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("x") or m.group(1).endswith("X")
def c_gn_ces_aux_pluriel_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_gn_plusieurs_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":[ipGWP]") and not (look(s[m.end():], "^ +(?:et|ou) ") and morph(dDA, nextword(s, m.end(), 2), ":[NAQ]", True, False))) or m.group(1) in aREGULARPLURAL
def s_gn_plusieurs_accord_1 (s, m):
    return suggPlur(m.group(1))
def c_gn_nombre_de_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":[ip]|>o(?:nde|xydation|or)\\b") and morphex(dDA, prevword1(s, m.start()), ":(?:G|[123][sp])", ":[AD]", True)) or m.group(1) in aREGULARPLURAL
def s_gn_nombre_de_accord_1 (s, m):
    return suggPlur(m.group(1))
def c_gn_det_plur_groupe_de_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":[ip]") or m.group(1) in aREGULARPLURAL
def s_gn_det_plur_groupe_de_accord_1 (s, m):
    return suggPlur(m.group(1))
def c_gn_det_sing_groupe_de_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":[ip]") or m.group(1) in aREGULARPLURAL
def s_gn_det_sing_groupe_de_accord_1 (s, m):
    return suggPlur(m.group(1))
def c_gn_quelque_adverbe2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":B.*:p", False) and m.group(2) != "cents"
def c_gn_nombre_lettres_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not re.search("(?i)^(janvier|février|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor)$", m.group(2))) or m.group(2) in aREGULARPLURAL
def s_gn_nombre_lettres_accord_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_neuf_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not morph(dDA, prevword1(s, m.start()), ":N", False) and not re.search("(?i)^(janvier|février|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor)$", m.group(2))) or m.group(2) in aREGULARPLURAL
def s_gn_neuf_accord_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_mille_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s") or m.group(1) in aREGULARPLURAL) and not look(s[:m.start()], r"(?i)\b(?:le|un|ce|du) +$")
def s_gn_mille_accord_1 (s, m):
    return suggPlur(m.group(1))
def c_gn_01_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p") and not re.search("(?i)^(janvier|février|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor|Rois|Corinthiens|Thessaloniciens)$", m.group(1))
def s_gn_01_accord_1 (s, m):
    return suggSing(m.group(1))
def c_gn_nombre_chiffres_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^0*[01]$", m.group(1)) and ((morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not re.search("(?i)^(janvier|février|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor)$", m.group(2))) or m.group(1) in aREGULARPLURAL)
def s_gn_nombre_chiffres_accord_1 (s, m):
    return suggPlur(m.group(2))
def c_gn_quel_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:p", ":(?:V0e|[NAQ].*:[me]:[si])")
def c_gn_quel_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quel_accord_2 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_quel_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m:p", ":(?:V0e|[NAQ].*:[me]:[si])")
def c_gn_quel_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_quel_accord_4 (s, m):
    return suggSing(m.group(2))
def c_gn_quel_accord_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:[si]", ":(?:V0e|[NAQ].*:[me]:[si])")
def c_gn_quel_accord_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quel_accord_6 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_quels_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:s", ":(?:V0e|[NAQ].*:[me]:[pi])")
def c_gn_quels_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quels_accord_2 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_quels_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m:s", ":(?:V0e|[NAQ].*:[me]:[pi])")
def c_gn_quels_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_quels_accord_4 (s, m):
    return suggPlur(m.group(2))
def c_gn_quels_accord_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:[pi]", ":(?:V0e|[NAQ].*:[me]:[pi])")
def c_gn_quels_accord_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quels_accord_6 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_quelle_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m:p", ":(?:V0e|[NAQ].*:[fe]:[si])")
def c_gn_quelle_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quelle_accord_2 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_quelle_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:p", ":(?:V0e|[NAQ].*:[fe]:[si])")
def c_gn_quelle_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_quelle_accord_4 (s, m):
    return suggSing(m.group(2))
def c_gn_quelle_accord_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m:[si]", ":(?:V0e|[NAQ].*:[fe]:[si])")
def c_gn_quelle_accord_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quelle_accord_6 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_quelles_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m:s", ":(?:V0e|[NAQ].*:[fe]:[pi])")
def c_gn_quelles_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quelles_accord_2 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_quelles_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f:s", ":(?:V0e|[NAQ].*:[fe]:[pi])")
def c_gn_quelles_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_quelles_accord_4 (s, m):
    return suggPlur(m.group(2))
def c_gn_quelles_accord_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m:[pi]", ":(?:V0e|[NAQ].*:[fe]:[pi])")
def c_gn_quelles_accord_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_quelles_accord_6 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_quel_quel_accord_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\btel(?:le|)s? +$")
def c_gn_quels_quelles_accord_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\btel(?:le|)s? +$")
def s_gn_quels_quelles_accord_être_1 (s, m):
    return m.group(1)[:-1]
def c_gn_quel_accord_être_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\btel(?:le|)s? +$") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f", ":[me]")
def c_gn_quelle_accord_être_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\btel(?:le|)s? +$") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":[fe]")
def c_gn_quels_accord_être_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\btel(?:le|)s? +$") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f", ":[me]")
def c_gn_quelles_accord_être_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\btel(?:le|)s? +$") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":[fe]")
def c_gn_quel_que_être_mas_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0e", False)
def c_gn_quel_que_être_mas_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0e", False) and morphex(dDA, (m.start(4), m.group(4)), ":[NAQ].*:m", ":[fe]")
def s_gn_quel_que_être_mas_1 (s, m):
    return m.group(1).replace("lle", "l")
def c_gn_quelle_que_être_fem_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0e", False)
def c_gn_quelle_que_être_fem_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0e", False) and morphex(dDA, (m.start(4), m.group(4)), ":[NAQ].*:f", ":[me]")
def s_gn_quelle_que_être_fem_1 (s, m):
    return m.group(1).replace("l", "lle")
def c_gn_trouver_ça_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">trouver ", False) and morphex(dDA, (m.start(3), m.group(3)), ":A.*:(?:f|m:p)", ":(?:G|3[sp]|M[12P])")
def s_gn_trouver_ça_adj_1 (s, m):
    return suggMasSing(m.group(3))
def c_gn_2m_accord_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ((morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m"))) and not apposition(m.group(1), m.group(2))
def s_gn_2m_accord_1 (s, m):
    return switchGender(m.group(2))
def c_gn_2m_accord_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_accord_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_accord_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return ((morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")) or (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s"))) and not apposition(m.group(1), m.group(2))
def s_gn_2m_accord_3 (s, m):
    return switchPlural(m.group(2))
def c_gn_2m_accord_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_2m_accord_4 (s, m):
    return switchPlural(m.group(1))
def c_gn_2m_pfx_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m")) ) and not apposition(m.group(1), m.group(2)) and morph(dDA, prevword1(s, m.start()), ":[VRX]", True, True)
def s_gn_2m_pfx_en_1 (s, m):
    return switchGender(m.group(2))
def c_gn_2m_pfx_en_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_pfx_en_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_pfx_en_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s")) or (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")) ) and not apposition(m.group(1), m.group(2)) and morph(dDA, prevword1(s, m.start()), ":[VRX]", True, True)
def s_gn_2m_pfx_en_3 (s, m):
    return switchPlural(m.group(2))
def c_gn_2m_pfx_en_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_2m_pfx_en_4 (s, m):
    return switchPlural(m.group(1))
def c_gn_2m_pfx_à_par_pour_sans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":[GYfe]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":[GYme]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m")) ) and not apposition(m.group(1), m.group(2)) and morph(dDA, prevword1(s, m.start()), ":[VRX]", True, True)
def s_gn_2m_pfx_à_par_pour_sans_1 (s, m):
    return switchGender(m.group(2))
def c_gn_2m_pfx_à_par_pour_sans_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_pfx_à_par_pour_sans_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_pfx_à_par_pour_sans_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p", ":[GYsi]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":[GYpi]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")) ) and not apposition(m.group(1), m.group(2)) and morph(dDA, prevword1(s, m.start()), ":[VRX]", True, True)
def s_gn_2m_pfx_à_par_pour_sans_3 (s, m):
    return switchPlural(m.group(2))
def c_gn_2m_pfx_à_par_pour_sans_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_2m_pfx_à_par_pour_sans_4 (s, m):
    return switchPlural(m.group(1))
def c_gn_2m_pfx_de_sur_avec_après_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:[Gfe]|V0e|Y)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":(?:[Gme]|V0e|Y)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m")) ) and not apposition(m.group(1), m.group(2)) and morph(dDA, prevword1(s, m.start()), ":[VRX]", True, True)
def s_gn_2m_pfx_de_sur_avec_après_1 (s, m):
    return switchGender(m.group(2))
def c_gn_2m_pfx_de_sur_avec_après_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_pfx_de_sur_avec_après_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_pfx_de_sur_avec_après_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p", ":(?:[Gsi]|V0e|Y)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", ":(?:[Gpi]|V0e|Y)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p")) ) and not apposition(m.group(1), m.group(2)) and morph(dDA, prevword1(s, m.start()), ":[VRX]", True, True)
def s_gn_2m_pfx_de_sur_avec_après_3 (s, m):
    return switchPlural(m.group(2))
def c_gn_2m_pfx_de_sur_avec_après_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def s_gn_2m_pfx_de_sur_avec_après_4 (s, m):
    return switchPlural(m.group(1))
def c_gn_de_manière_façon_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":A.*:(m|f:p)", ":[GM]")
def s_gn_de_manière_façon_1 (s, m):
    return suggFemSing(m.group(2))
def c_gn_2m_l_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^air$", m.group(1)) and not m.group(2).startswith("seul") and ( (morph(dDA, (m.start(1), m.group(1)), ":m") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morph(dDA, (m.start(1), m.group(1)), ":f") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m")) ) and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_l_1 (s, m):
    return switchGender(m.group(2), False)
def c_gn_2m_l_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_l_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_l_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^air$", m.group(1)) and not m.group(2).startswith("seul") and morph(dDA, (m.start(1), m.group(1)), ":[si]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_l_3 (s, m):
    return suggSing(m.group(2))
def c_gn_2m_l_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and ( (morph(dDA, (m.start(1), m.group(1)), ":m") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morph(dDA, (m.start(1), m.group(1)), ":f") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m")) ) and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]", False, False)
def s_gn_2m_l_après_et_ou_de_1 (s, m):
    return switchGender(m.group(2), False)
def c_gn_2m_l_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_l_après_et_ou_de_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_l_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^air$", m.group(1)) and not m.group(2).startswith("seul") and morph(dDA, (m.start(1), m.group(1)), ":[si]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]", False, False)
def s_gn_2m_l_après_et_ou_de_3 (s, m):
    return suggSing(m.group(2))
def c_gn_2m_un_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_un_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_2m_un_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p") and not m.group(2).startswith("seul") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|d’) *$")
def s_gn_2m_un_2 (s, m):
    return suggMasSing(m.group(2))
def c_gn_2m_un_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_un_après_et_ou_de_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_2m_un_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p") and not m.group(2).startswith("seul") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQB]|>(?:et|ou) ", False, False)
def s_gn_2m_un_après_et_ou_de_2 (s, m):
    return suggMasSing(m.group(2))
def c_gn_2m_une_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_une_1 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_2m_une_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p") and not m.group(2).startswith("seul") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|d’) *$")
def s_gn_2m_une_2 (s, m):
    return suggFemSing(m.group(2))
def c_gn_2m_une_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_une_après_et_ou_de_1 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_2m_une_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p") and not m.group(2).startswith("seul") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQB]|>(?:et|ou) ", False, False)
def s_gn_2m_une_après_et_ou_de_2 (s, m):
    return suggFemSing(m.group(2))
def c_gn_2m_le_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_le_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f") and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_le_2 (s, m):
    return suggMasSing(m.group(3), True)
def c_gn_2m_le_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_le_3 (s, m):
    return suggMasSing(m.group(3))
def c_gn_2m_le_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_le_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f") and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_le_après_et_ou_de_2 (s, m):
    return suggMasSing(m.group(3), True)
def c_gn_2m_le_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_le_après_et_ou_de_3 (s, m):
    return suggMasSing(m.group(3))
def c_gn_2m_det_mas_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_mas_sing_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_2m_det_mas_sing_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_mas_sing_2 (s, m):
    return suggMasSing(m.group(2))
def c_gn_2m_det_mas_sing_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_mas_sing_après_et_ou_de_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_2m_det_mas_sing_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_mas_sing_après_et_ou_de_2 (s, m):
    return suggMasSing(m.group(2))
def c_gn_2m_mon_ton_son_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:B|G|e|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_mon_ton_son_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_2m_mon_ton_son_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_mon_ton_son_2 (s, m):
    return suggMasSing(m.group(2))
def c_gn_2m_mon_ton_son_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:B|G|e|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_mon_ton_son_après_et_ou_de_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_2m_mon_ton_son_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_mon_ton_son_après_et_ou_de_2 (s, m):
    return suggMasSing(m.group(2))
def c_gn_2m_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_la_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m") and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_la_2 (s, m):
    return suggFemSing(m.group(3), True)
def c_gn_2m_la_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_la_3 (s, m):
    return suggFemSing(m.group(3))
def c_gn_2m_la_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_la_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m") and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_la_après_et_ou_de_2 (s, m):
    return suggFemSing(m.group(3), True)
def c_gn_2m_la_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_la_après_et_ou_de_3 (s, m):
    return suggFemSing(m.group(3))
def c_gn_2m_det_fem_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_fem_sing_1 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_2m_det_fem_sing_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_fem_sing_2 (s, m):
    return suggFemSing(m.group(2))
def c_gn_2m_det_fem_sing_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_fem_sing_après_et_ou_de_1 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_2m_det_fem_sing_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_fem_sing_après_et_ou_de_2 (s, m):
    return suggFemSing(m.group(2))
def c_gn_2m_leur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_leur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and ((morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m"))) and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_leur_2 (s, m):
    return switchGender(m.group(3), False)
def c_gn_2m_leur_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_2m_leur_3 (s, m):
    return switchGender(m.group(1), False)
def c_gn_2m_leur_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_leur_4 (s, m):
    return suggSing(m.group(3))
def c_gn_2m_leur_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_leur_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and ((morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m"))) and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_leur_après_et_ou_de_2 (s, m):
    return switchGender(m.group(3), False)
def c_gn_2m_leur_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_2m_leur_après_et_ou_de_3 (s, m):
    return switchGender(m.group(1), False)
def c_gn_2m_leur_après_et_ou_de_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(3).startswith("seul") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_leur_après_et_ou_de_4 (s, m):
    return suggSing(m.group(3))
def c_gn_2m_det_epi_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and not re.search("(?i)^quelque chose", m.group(0)) and ((morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m"))) and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_epi_sing_1 (s, m):
    return switchGender(m.group(2), False)
def c_gn_2m_det_epi_sing_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_det_epi_sing_2 (s, m):
    return switchGender(m.group(1), False)
def c_gn_2m_det_epi_sing_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_epi_sing_3 (s, m):
    return suggSing(m.group(2))
def c_gn_2m_det_epi_sing_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and not re.search("(?i)quelque chose", m.group(0)) and ((morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m"))) and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_epi_sing_après_et_ou_de_1 (s, m):
    return switchGender(m.group(2), False)
def c_gn_2m_det_epi_sing_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_det_epi_sing_après_et_ou_de_2 (s, m):
    return switchGender(m.group(1), False)
def c_gn_2m_det_epi_sing_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWsi]") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_epi_sing_après_et_ou_de_3 (s, m):
    return suggSing(m.group(2))
def c_gn_2m_det_mas_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_mas_plur_1 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_2m_det_mas_plur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", ":G") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not look(s[:m.start()], r"(?i)\bune de ")
def s_gn_2m_det_mas_plur_2 (s, m):
    return suggMasPlur(m.group(2))
def c_gn_2m_det_mas_plur_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[me]", ":(?:B|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_mas_plur_après_et_ou_de_1 (s, m):
    return suggMasPlur(m.group(2), True)
def c_gn_2m_det_mas_plur_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", ":G") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not ( look(s[:m.start()], r"(?i)\bune? de ") or (m.group(0).startswith("de") and look(s[:m.start()], r"(?i)\bune? +$")) )
def s_gn_2m_det_mas_plur_après_et_ou_de_2 (s, m):
    return suggMasPlur(m.group(2))
def c_gn_2m_det_fem_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m") and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_fem_plur_1 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_2m_det_fem_plur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not look(s[:m.start()], r"(?i)\bune de ")
def s_gn_2m_det_fem_plur_2 (s, m):
    return suggFemPlur(m.group(2))
def c_gn_2m_det_fem_plur_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m") and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_fem_plur_après_et_ou_de_1 (s, m):
    return suggFemPlur(m.group(2), True)
def c_gn_2m_det_fem_plur_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).startswith("seul") and morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not ( look(s[:m.start()], r"(?i)\bune? de ") or (m.group(0).startswith("de") and look(s[:m.start()], r"(?i)\bune? +$")) )
def s_gn_2m_det_fem_plur_après_et_ou_de_2 (s, m):
    return suggFemPlur(m.group(2))
def c_gn_2m_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_les_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and ((morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m"))) and not apposition(m.group(2), m.group(3)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_les_2 (s, m):
    return switchGender(m.group(3), True)
def c_gn_2m_les_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_2m_les_3 (s, m):
    return switchGender(m.group(1), True)
def c_gn_2m_les_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s") and not apposition(m.group(2), m.group(3)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not look(s[:m.start()], r"(?i)\bune? de ")
def s_gn_2m_les_4 (s, m):
    return suggPlur(m.group(3))
def c_gn_2m_les_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def c_gn_2m_les_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and ((morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m"))) and not apposition(m.group(2), m.group(3)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_les_après_et_ou_de_2 (s, m):
    return switchGender(m.group(3), True)
def c_gn_2m_les_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(2))
def s_gn_2m_les_après_et_ou_de_3 (s, m):
    return switchGender(m.group(1), True)
def c_gn_2m_les_après_et_ou_de_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "fois" and not m.group(3).startswith("seul") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s") and not apposition(m.group(2), m.group(3)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not ( look(s[:m.start()], r"(?i)\bune? de ") or (m.group(0).startswith("de") and look(s[:m.start()], r"(?i)\bune? +$")) )
def s_gn_2m_les_après_et_ou_de_4 (s, m):
    return suggPlur(m.group(3))
def c_gn_2m_det_epi_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and ((morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m"))) and not apposition(m.group(1), m.group(2)) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_gn_2m_det_epi_plur_1 (s, m):
    return switchGender(m.group(2), True)
def c_gn_2m_det_epi_plur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_det_epi_plur_2 (s, m):
    return switchGender(m.group(1), True)
def c_gn_2m_det_epi_plur_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not look(s[:m.start()], r"(?i)\bune? de ")
def s_gn_2m_det_epi_plur_3 (s, m):
    return suggPlur(m.group(2))
def c_gn_2m_det_epi_plur_après_et_ou_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and ((morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":(?:B|e|G|V0|f)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":(?:B|e|G|V0|m)") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m"))) and not apposition(m.group(1), m.group(2)) and not morph(dDA, prevword1(s, m.start()), ":[NAQ]|>(?:et|ou) ", False, False)
def s_gn_2m_det_epi_plur_après_et_ou_de_1 (s, m):
    return switchGender(m.group(2), True)
def c_gn_2m_det_epi_plur_après_et_ou_de_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_det_epi_plur_après_et_ou_de_2 (s, m):
    return switchGender(m.group(1), True)
def c_gn_2m_det_epi_plur_après_et_ou_de_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and not ( look(s[:m.start()], r"(?i)\bune? de ") or (m.group(0).startswith("de") and look(s[:m.start()], r"(?i)\bune? +$")) )
def s_gn_2m_det_epi_plur_après_et_ou_de_3 (s, m):
    return suggPlur(m.group(2))
def c_gn_2m_des_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "fois" and not m.group(2).startswith("seul") and ( (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":[fe]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f")) or (morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f", ":[me]") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m")) ) and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and morph(dDA, prevword1(s, m.start()), ":[VRBX]|>comme ", True, True)
def s_gn_2m_des_1 (s, m):
    return switchGender(m.group(2), True)
def c_gn_2m_des_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and hasFemForm(m.group(1))
def s_gn_2m_des_2 (s, m):
    return switchGender(m.group(1))
def c_gn_2m_des_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s") and not apposition(m.group(1), m.group(2)) and not (look_chk1(dDA, s[m.end():], m.end(), r"^ +et +(\w[\w-]+)", ":A") or look_chk1(dDA, s[m.end():], m.end(), r"^ *, +(\w[\w-]+)", ":A.*:[si]")) and (morphex(dDA, (m.start(2), m.group(2)), ":N", ":[AQ]") or morph(dDA, prevword1(s, m.start()), ":[VRBX]|>comme ", True, True))
def s_gn_2m_des_3 (s, m):
    return suggPlur(m.group(2))
def c_gn_2m_des_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return checkAgreement(m.group(1), m.group(2))
def d_gn_2m_des_4 (s, m, dDA):
    return exclude(dDA, m.start(2), m.group(2), ":V")
def c_gn_3m_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s")) or (morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s") and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p"))
def s_gn_3m_1 (s, m):
    return switchPlural(m.group(3))
def c_gn_3m_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]") and morph(dDA, (m.start(3), m.group(3)), ":[NAQ].*:[pi]") and morph(dDA, (m.start(4), m.group(4)), ":[NAQ].*:s")
def s_gn_3m_les_1 (s, m):
    return suggPlur(m.group(4))
def c_gn_3m_le_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", False) and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:[si]", ":G") and morph(dDA, (m.start(4), m.group(4)), ":[NAQ].*:p")
def s_gn_3m_le_la_1 (s, m):
    return suggSing(m.group(4))
def c_gn_3m_det_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", False) and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:[si]", ":G") and morph(dDA, (m.start(4), m.group(4)), ":[NAQ].*:p")
def s_gn_3m_det_sing_1 (s, m):
    return suggSing(m.group(4))
def c_gn_3m_det_plur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:[pi]", ":G") and morph(dDA, (m.start(4), m.group(4)), ":[NAQ].*:s") and not look(s[:m.start()], r"(?i)\bune? de ")
def s_gn_3m_det_plur_1 (s, m):
    return suggPlur(m.group(4))
def c_gn_devinette1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:(?:m|f:p)", ":(?:G|P|[fe]:[is]|V0|3[sp])") and not apposition(m.group(1), m.group(2))
def s_gn_devinette1_1 (s, m):
    return suggFemSing(m.group(2), True)
def c_gn_devinette2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and not apposition(m.group(1), m.group(2))
def s_gn_devinette2_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_devinette3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:f|>[aéeiou].*:e", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:(?:f|m:p)", ":(?:G|P|m:[is]|V0|3[sp])") and not apposition(m.group(1), m.group(2))
def s_gn_devinette3_1 (s, m):
    return suggMasSing(m.group(2), True)
def c_gn_devinette4_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":G|>[aéeiou].*:[ef]") and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and not apposition(m.group(2), m.group(3))
def s_gn_devinette4_1 (s, m):
    return suggMasSing(m.group(3), True)
def c_gn_devinette5_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:m", ":G|>[aéeiou].*:[ef]") and not morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f|>[aéeiou].*:e", False) and morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and not apposition(m.group(2), m.group(3))
def s_gn_devinette5_1 (s, m):
    return suggMasSing(m.group(3), True)
def c_gn_devinette6_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":(?:G|P|[me]:[ip]|V0|3[sp])") and not apposition(m.group(1), m.group(2))
def s_gn_devinette6_1 (s, m):
    return suggPlur(m.group(2))
def c_sgpl_prep_attendu_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_sgpl_prep_étant_donné_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_sgpl_prep_vu_det_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_sgpl_vingt_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\bquatre $")
def c_sgpl_quatre_vingt_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":B", False) and not look(s[:m.start()], r"(?i)\b(?:numéro|page|chapitre|référence|année|test|série)s? +$")
def s_sgpl_xxx_neuf_1 (s, m):
    return m.group(0)[:-1]
def c_sgpl_xxx_cents_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":B|>une?", False, True) and not look(s[:m.start()], r"(?i)\b(?:numéro|page|chapitre|référence|année|test|série)s? +$")
def c_sgpl_xxx_cent_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, nextword1(s, m.end()), ":B|>une?", False, False)
def c_sgpl_cents_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", ":G") and morphex(dDA, prevword1(s, m.start()), ":[VR]", ":B", True)
def c_sgpl_mille_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, nextword1(s, m.end()), ":B|:N.*:p", ":[QA]", False) or (morph(dDA, prevword1(s, m.start()), ":B") and morph(dDA, nextword1(s, m.end()), ":[NAQ]", False))
def c_sgpl_collectif_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":D.*:[si]", False, True)
def s_sgpl_confluence_de_1 (s, m):
    return suggPlur(m.group(1))
def s_sgpl_troupeau_de_1 (s, m):
    return suggPlur(m.group(1))
def s_sgpl_x_fois_par_période_1 (s, m):
    return suggSing(m.group(1))
def c_sgpl_à_nu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:mettre|mise) ", False)
def c_sgpl_faire_affaire_avec_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False)
def c_sgpl_faire_affaire_à_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False) and morph(dDA, (m.start(3), m.group(3)), ":(?:N|MP)")
def s_sgpl_à_l_intérieur_extérieur_1 (s, m):
    return m.group(1).rstrip("e")
def c_sgpl_collet_monté_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:V0e|W)|>très", False)
def c_sgpl_coûter_cher_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:co[ûu]ter|payer) ", False)
def c_sgpl_donner_lieu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">donner ", False)
def c_sgpl_ensemble_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:[123]p|>(?:tou(?:te|)s|pas|rien|guère|jamais|toujours|souvent) ", ":[DRB]")
def c_sgpl_avoir_pied_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:avoir|perdre) ", False)
def c_sgpl_à_pied_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:lit|fauteuil|armoire|commode|guéridon|tabouret|chaise)s?\b")
def c_sgpl_plein_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, prevword1(s, m.start()), ":(?:V|[NAQ].*:s)", ":(?:[NA]:.:[pi]|V0e.*:[123]p)", True)
def c_conf_ce_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (look(s[m.end():], "^ [ldmtsc]es ") and not look(s[:m.start()], r"(?i)\b(?:ils?|elles?|ne) +")) or ( morph(dDA, prevword1(s, m.start()), ":Cs", False, True) and not look(s[:m.start()], ", +$") and not look(s[m.end():], r"(?i)^ +(?:ils?|elles?)\b") and not morph(dDA, nextword1(s, m.end()), ":Q", False, False) )
def c_sgpl_bonnes_vacances_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:f:s", False, False)
def c_sgpl_en_vacances_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:aller|partir) ", False)
def c_sgpl_vite_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":V0e.*:3p", False, False) or morph(dDA, nextword1(s, m.end()), ":Q", False, False)
def c_conf_suite_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":D|>[ld] ", False) and look(s[:m.start()], "^ *$|, *$")
def c_conf_pronom_à_l_air_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[AR]", ">libre ") and morph(dDA, prevword1(s, m.start()), ":Cs", False, True)
def c_conf_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:il |elle |n’) *$")
def s_conf_acre_1 (s, m):
    return m.group(1).replace("â", "a").replace("Â", "A")
def c_conf_âcre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ">(?:être|go[ûu]t|humeur|odeur|parole|parfum|remarque|reproche|réponse|saveur|senteur|sensation|vin)", False, False)
def s_conf_âcre_1 (s, m):
    return m.group(0).replace("a", "â").replace("A", "Â")
def c_conf_être_accro_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:être|devenir|para[îi]tre|rendre|sembler) ", False)
def s_conf_être_accro_1 (s, m):
    return m.group(2).replace("oc", "o")
def s_conf_accro_à_1 (s, m):
    return m.group(1).replace("oc", "o")
def c_conf_tenir_pour_acquit_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tenir ")
def c_conf_à_l_amende_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mettre ", False)
def c_conf_faire_amende_honorable_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False)
def c_conf_hospice1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:être|aller) ", False)
def s_conf_hospice2_1 (s, m):
    return m.group(1).replace("auspice", "hospice")
def s_conf_hospice3_1 (s, m):
    return m.group(1).replace("auspice", "hospice").replace("Auspice", "Hospice")
def s_conf_arrière_ban_1 (s, m):
    return m.group(0).replace("c", "").replace("C", "")
def c_conf_mettre_au_ban_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">mettre ", False) and not look(s[m.end():], "^ +des accusés")
def c_conf_publier_les_bans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">publi(?:er|cation) ", False)
def c_conf_bel_et_bien_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":[AQ]")
def s_conf_bitte_1 (s, m):
    return m.group(0).replace("ite", "itte")
def c_conf_en_bonne_et_due_forme_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "bonne et due forme"
def c_conf_c_est_était_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":[AM]", ":[QG]")
def s_conf_canne_à_de_1 (s, m):
    return m.group(1).replace("cane", "canne")
def c_conf_verbe_canne_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:appuyer|battre|frapper|lever|marcher) ", False)
def s_conf_verbe_canne_1 (s, m):
    return m.group(2).replace("cane", "canne")
def c_conf_ville_de_Cannes1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^C(?:annes|ANNES)", m.group(1))
def c_conf_ville_de_Cannes2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^C(?:annes|ANNES)", m.group(1))
def c_conf_faire_bonne_chère_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False)
def s_conf_champ_de_1 (s, m):
    return m.group(1).replace("nt", "mp")
def c_conf_être_censé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False) and morph(dDA, (m.start(3), m.group(3)), ":(?:Y|Oo)", False)
def s_conf_être_censé_1 (s, m):
    return m.group(2).replace("sens", "cens")
def s_conf_sensé_1 (s, m):
    return m.group(1).replace("c", "s").replace("C", "S")
def c_conf_content_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_conf_argent_comptant_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":[VR]", False)
def c_conf_à_cor_et_à_cri_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^à cor et à cri$", m.group(0))
def s_conf_côté_1 (s, m):
    return m.group(1).replace("o", "ô")
def s_conf_côte_1 (s, m):
    return m.group(1).replace("o", "ô").replace("tt", "t")
def s_conf_cote_1 (s, m):
    return m.group(1).replace("ô", "o").replace("tt", "t")
def s_conf_cotte_1 (s, m):
    return m.group(1).replace("ô", "o").replace("t", "tt")
def c_conf_avoir_la_cote_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_conf_tordre_le_cou_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tordre ", False)
def c_conf_rendre_coup_pour_coup_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">rendre ", False)
def c_conf_couper_court_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">couper ")
def c_conf_laisser_libre_cours_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:avoir|donner|laisser) ", False)
def c_conf_dès_que_lors1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:[lmtsc]es|des?|[nv]os|leurs|quels) +$")
def c_conf_erreur_problème_decelé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:desceller|desseller) ", False)
def s_conf_erreur_problème_decelé_1 (s, m):
    return m.group(2).replace("escell", "écel").replace("essell", "écel")
def c_conf_deceler_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:desceller|desseller) ", False)
def s_conf_deceler_qqch_1 (s, m):
    return m.group(1).replace("escell", "écel").replace("essell", "écel")
def c_conf_en_train_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ">(?:être|voyager|surprendre|venir|arriver|partir|aller) ", False, False) or look(s[:m.start()], "-(?:ils?|elles?|on|je|tu|nous|vous) +$")
def c_conf_entrain_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ">(?:avec|sans|quel(?:le|)|cet|votre|notre|mon|leur) ", False, False) or look(s[:m.start()], " [dlDL]’$")
def c_conf_à_l_envi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ">(?:abandonner|céder|résister) ", False) and not look(s[m.end():], "^ d(?:e |’)")
def c_conf_est_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[QA]", ":M") and m.group(2).islower()
def c_conf_est_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return look_chk1(dDA, s[:m.start()], 0, r"(?i)^ *(?:l[ea]|ce(?:tte|t|)|mon|[nv]otre) +(\w[\w-]+\w) +$", ":[NA].*:[is]", ":G")
def c_conf_est_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return look_chk1(dDA, s[:m.start()], 0, r"(?i)^ *(?:ton) +(\w[\w-]+\w) +$", ":N.*:[is]", ":[GA]")
def c_conf_est_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return look_chk1(dDA, s[:m.start()], 0, r"^ *([A-ZÉÈ][\w-]+\w) +$", ":M", ":G")
def c_conf_où_est_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":D", ":R|>(?:quand|pourquoi)") or (m.group(2) == "l" and look(s[m.end():], "^’"))
def c_conf_faites_vous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D.*:[me]:[sp]", False)
def c_conf_avoir_être_faite_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0", False)
def s_conf_avoir_être_faite_1 (s, m):
    return m.group(2).replace("î", "i")
def c_conf_en_fait_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:[vn]ous|lui|leur|et toi) +$|[nm]’$")
def s_conf_flamant_rose_1 (s, m):
    return m.group(1).replace("and", "ant")
def c_conf_bonne_mauvaise_foi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not ( m.group(1) == "bonne" and look(s[:m.start()], r"(?i)\bune +$") and look(s[m.end():], "(?i)^ +pour toute") )
def c_conf_faire_perdre_donner_foi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:faire|perdre|donner|avoir) ", False)
def c_conf_glacière_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":D", False)
def s_conf_goutte_1 (s, m):
    return m.group(1).replace("û", "u").replace("t", "tt")
def s_conf_jeûne_1 (s, m):
    return m.group(1).replace("u", "û")
def s_conf_jeune_1 (s, m):
    return m.group(1).replace("û", "u")
def s_conf_celui_celle_là_1 (s, m):
    return m.group(0)[:-1].replace(" ", "-")+"à"
def c_conf_verbe_impératif_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":[NAQ]")
def c_conf_mot_là_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":[123][sp]")
def c_conf_il_elle_on_la_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[123][sp]", ":[GQ]")
def c_conf_ne_la_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[123][sp]", ":[GQ]")
def c_conf_me_se_se_la_vconj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[123][sp]", ":[GQ]")
def c_conf_il_elle_on_l_a_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":Q", ":(?:[123][sp]|V[123]......e)|>lui ")
def c_conf_ne_l_a_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":Q", ":(?:[123][sp]|V[123]......e)|>lui ")
def c_conf_me_te_l_a_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":Q", ":(?:[123][sp]|V[123]......e)|>lui ")
def s_conf_lever_de_rideau_soleil_1 (s, m):
    return m.group(0).replace("ée", "er")
def c_conf_lever_un_lièvre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">soulever ", False)
def s_conf_lever_un_lièvre_1 (s, m):
    return m.group(1)[3:]
def c_conf_être_à_xxx_lieues_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:être|habiter|trouver|situer|rester|demeurer?) ", False)
def c_conf_avoir_eu_lieu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False)
def c_conf_marre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"(?i)(?:la|une|cette|quelle|cette|[mts]a) +$")
def c_conf_avoir_marre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_conf_avoir_mis_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_conf_les_nôtres_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (m.group(1) == "Notre" and look(s[m.end():], "Père"))
def s_conf_les_nôtres_1 (s, m):
    return m.group(1).replace("otre", "ôtre")
def c_conf_notre_votre_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(les?|la|du|des|aux?) +") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ]", ":D")
def s_conf_notre_votre_qqch_1 (s, m):
    return m.group(1).replace("ôtre", "otre").rstrip("s")
def c_conf_nulle_part_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":D", False, False)
def c_conf_on1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_conf_on2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( re.search("^[nmts]e$", m.group(2)) or (not re.search("(?i)^(?:confiance|envie|peine|prise|crainte|affaire|hâte|force|recours|somme)$", m.group(2)) and morphex(dDA, (m.start(2), m.group(2)), ":[0123][sp]", ":[QG]")) ) and morph(dDA, prevword1(s, m.start()), ":Cs", False, True)
def c_conf_on3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:(?:[1-3][sp])", ":(?:G|1p)") and not ( m.group(0).find(" leur ") and morph(dDA, (m.start(2), m.group(2)), ":[NA].*:[si]", False) ) and look(s[:m.start()], "^ *$|, *$")
def c_conf_on6_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":[VR]", False, False) and not morph(dDA, nextword1(s, m.end()), ":(?:3s|Oo|X)", False)
def c_conf_xxx_on2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":3s", False) and look(s[:m.start()], "^ *$|, $")
def s_conf_pain_qqch_1 (s, m):
    return m.group(1).replace("pin", "pain")
def c_conf_manger_pain_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:manger|dévorer|avaler|engloutir) ")
def s_conf_manger_pain_1 (s, m):
    return m.group(2).replace("pin", "pain")
def c_conf_aller_de_pair_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">aller ", False)
def c_conf_être_pâle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def s_conf_être_pâle_1 (s, m):
    return m.group(2).replace("pal", "pâl")
def s_conf_qqch_pâle_1 (s, m):
    return m.group(1).replace("pal", "pâl")
def c_conf_prendre_parti_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">prendre ", False)
def c_conf_tirer_parti_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">tirer ", False)
def c_conf_faire_partie_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False)
def c_conf_prendre_à_partie_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">prendre ", False)
def c_conf_pâtes_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return re.search("(?i)^pattes?", m.group(1))
def s_conf_pâtes_1 (s, m):
    return m.group(1).replace("att", "ât")
def c_conf_pâtes_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).startswith("d’amende")
def c_conf_pâtes_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).startswith("a ")
def s_conf_pâtes_3 (s, m):
    return m.group(2).replace("a ", "à ")
def c_conf_peu_de_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ]")
def c_conf_peut_être_adverbe1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:N|A|Q|G|MP)")
def c_conf_diagnostic_pronostique_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( m.group(0).endswith("s") and look(s[:m.start()], r"(?i)\b(?:[mtscd]es|[nv]os|leurs|quels) $") ) or ( m.group(0).endswith("e") and look(s[:m.start()], r"(?i)\b(?:mon|ce|quel|un|du|[nv]otre) $") )
def s_conf_diagnostic_pronostique_1 (s, m):
    return m.group(0).replace("que", "c")
def c_conf_pu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_conf__1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, nextword1(s, m.end()), ":(?:Os|C)", False, True)
def c_conf_quoi_qu_il_en_soit_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":[AQ]", False)
def c_conf_quoi_qu_il_en_coûte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "^ *$|^,")
def c_conf_raisonner_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">résonner ", False)
def s_conf_raisonner_1 (s, m):
    return m.group(1).replace("réso", "raiso")
def c_conf_saint_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":M1", False) and morph(dDA, prevword1(s, m.start()), ":(?:R|[123][sp])", False, True)
def s_conf_salle_qqch_1 (s, m):
    return m.group(1).replace("sale", "salle")
def c_conf_être_sale_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def s_conf_être_sale_1 (s, m):
    return m.group(2).replace("salle", "sale")
def s_conf_qqch_septique_1 (s, m):
    return m.group(1).replace("scep","sep")
def c_conf_être_sceptique_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:être|demeurer) ", False)
def s_conf_être_sceptique_1 (s, m):
    return m.group(2).replace("sep", "scep")
def c_conf_s_ensuivre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">suivre ", False)
def c_conf_soi_disant_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^soi-disant$", m.group(0))
def c_conf_prep_soi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[m.end():], " soit ")
def c_conf_en_soi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, nextword1(s, m.end()), ":[GY]", True, True) and not look(s[:m.start()], "(?i)quel(?:s|les?|) qu $|on $|il $") and not look(s[m.end():], " soit ")
def c_conf_soi_même1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, prevword1(s, m.start()), ":[YQ]|>(?:avec|contre|par|pour|sur) ", False, True)
def c_conf_soit1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and morphex(dDA, (m.start(2), m.group(2)), ":[OC]", ":R")
def c_conf_soit2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def s_conf_sûr_que_1 (s, m):
    return m.group(1).replace("sur", "sûr")
def s_conf_sûre_surs_de_1 (s, m):
    return m.group(1).replace("sur", "sûr")
def c_conf_sûr_de_vinfi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":Y", False)
def s_conf_sûr_de_vinfi_1 (s, m):
    return m.group(1).replace("sur", "sûr")
def c_conf_tache_de_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":N", ":[GMY]|>(?:fonds?|grande (?:envergure|ampleur|importance)|envergure|ampleur|importance|départ|surveillance) ") and not look(s[:m.start()], "accompl|dél[éè]gu")
def s_conf_tache_de_qqch_1 (s, m):
    return m.group(1).replace("â", "a")
def s_conf_tache_adjectif_1 (s, m):
    return m.group(1).replace("â", "a")
def c_conf_aller_en_taule_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">aller ", False)
def c_conf_faire_de_la_taule_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False)
def s_conf_tôle_qqch_1 (s, m):
    return m.group(1).replace("au", "ô")
def c_conf_il_être_tant_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False) and morph(dDA, (m.start(3), m.group(3)), ":Y|>(?:ne|en|y) ", False)
def c_conf_avoir_tort_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:avoir|donner) ", False)
def s_conf_qqch_venimeux_1 (s, m):
    return m.group(1).replace("énén", "enim")
def s_conf_qqch_vénéneux_1 (s, m):
    return m.group(1).replace("enim", "énén")
def s_conf_ver_de_terre_1 (s, m):
    return m.group(1).replace("re", "").replace("t", "")
def c_conf_vieil_euphonie_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[me]:s")
def c_mc_mot_composé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(1).isdigit() and not m.group(2).isdigit() and not morph(dDA, (m.start(0), m.group(0)), ":", False) and not morph(dDA, (m.start(2), m.group(2)), ":G", False) and _oSpellChecker.isValid(m.group(1)+m.group(2))
def c_mc_mot_composé_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) != "là" and not re.search("(?i)^(?:ex|mi|quasi|semi|non|demi|pro|anti|multi|pseudo|proto|extra)$", m.group(1)) and not m.group(1).isdigit() and not m.group(2).isdigit() and not morph(dDA, (m.start(2), m.group(2)), ":G", False) and not morph(dDA, (m.start(0), m.group(0)), ":", False) and not _oSpellChecker.isValid(m.group(1)+m.group(2))
def c_maj_jours_semaine_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"[\w,] +$")
def s_maj_jours_semaine_1 (s, m):
    return m.group(0).lower()
def c_maj_mois_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"[\w,] +$") and not( ( m.group(0)=="Juillet" and look(s[:m.start()], "(?i)monarchie +de +$") ) or ( m.group(0)=="Octobre" and look(s[:m.start()], "(?i)révolution +d’$") ) )
def s_maj_mois_1 (s, m):
    return m.group(0).lower()
def c_maj_qqch_de_l_État_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^fonctions? ", m.group(0)) or not look(s[:m.start()], r"(?i)\ben $")
def s_maj_État_nation_providence_1 (s, m):
    return m.group(1).replace("é", "É")
def c_maj_gentilés_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).istitle() and morphex(dDA, (m.start(1), m.group(1)), ":N", ":(?:A|V0e|D|R|B)") and not re.search("^([oO]céan Indien|[îÎiI]les Britanniques)", m.group(0))
def s_maj_gentilés_1 (s, m):
    return m.group(2).lower()
def c_maj_gentilés_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).islower() and not m.group(2).startswith("canadienne") and ( re.search("(?i)^(?:certaine?s?|cette|ce[ts]?|[dl]es|[nv]os|quelques|plusieurs|chaque|une|aux)$", m.group(1)) or ( re.search("(?i)^un$", m.group(1)) and not look(s[m.end():], "(?:approximatif|correct|courant|parfait|facile|aisé|impeccable|incompréhensible)") and not look(s[:m.start()], r"(?i)\bdans +")) )
def s_maj_gentilés_2 (s, m):
    return m.group(2).capitalize()
def s_maj_gentilés2_1 (s, m):
    return m.group(1).capitalize()
def c_maj_langues_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:parler|cours|leçon|apprendre|étudier|traduire|enseigner|professeur|enseignant|dictionnaire|méthode) ", False)
def s_maj_langues_1 (s, m):
    return m.group(2).lower()
def s_maj_en_langue_1 (s, m):
    return m.group(1).lower()
def c_maj_église_qqch_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], r"\w")
def s_maj_qqch_du_Nord_Sud_1 (s, m):
    return m.group(1).capitalize()
def s_maj_qqch_de_l_Ouest_Est_1 (s, m):
    return m.group(1).capitalize()
def c_maj_unités_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return re.search("^(?:Mètre|Watt|Gramme|Seconde|Ampère|Kelvin|Mole|Cand[eé]la|Hertz|Henry|Newton|Pascal|Joule|Coulomb|Volt|Ohm|Farad|Tesla|W[eé]ber|Radian|Stéradian|Lumen|Lux|Becquerel|Gray|Sievert|Siemens|Katal)s?|(?:Exa|P[ée]ta|Téra|Giga|Méga|Kilo|Hecto|Déc[ai]|Centi|Mi(?:lli|cro)|Nano|Pico|Femto|Atto|Ze(?:pto|tta)|Yo(?:cto|etta))(?:mètre|watt|gramme|seconde|ampère|kelvin|mole|cand[eé]la|hertz|henry|newton|pascal|joule|coulomb|volt|ohm|farad|tesla|w[eé]ber|radian|stéradian|lumen|lux|becquerel|gray|sievert|siemens|katal)s?", m.group(2))
def s_maj_unités_1 (s, m):
    return m.group(2).lower()
def c_infi_à_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":Y")
def s_infi_à_en_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V1") and not m.group(1)[0:1].isupper() and (m.group(1).endswith("z") or not look(s[:m.start()], r"(?i)\b(?:quelqu(?:e chose|’une?)|(?:l(es?|a)|nous|vous|me|te|se)[ @]trait|personne|point +$|rien(?: +[a-zéèêâîûù]+|) +$)"))
def s_infi_de_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_de_nous_vous_lui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V1", ":M[12P]")
def s_infi_de_nous_vous_lui_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_de_le_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V1", False)
def s_infi_de_le_les_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":[123][sp]")
def c_infi_pour_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V1", ":[NM]") and not morph(dDA, prevword1(s, m.start()), ">(?:tenir|passer) ", False)
def s_infi_pour_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_pour_nous_vous_lui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V1", False)
def s_infi_pour_nous_vous_lui_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_sans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V1", ":[NM]")
def s_infi_sans_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_nous_vous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":Q", False) and not morph(dDA, prevword1(s, m.start()), "V0.*[12]p", False)
def c_infi_devoir_savoir_pouvoir_interrogatif_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:devoir|savoir|pouvoir|vouloir) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":(?:Q|A|[123][sp])", ":[GYW]")
def s_infi_devoir_savoir_pouvoir_interrogatif_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_est_ce_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:V1.*:Q|[13]s|2[sp])", ":[GYWM]") and not look(s[:m.start()], r"(?i)\bque? +$")
def s_infi_est_ce_que_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_commencer_finir_par_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:commencer|finir) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":V", ":[NGM]") and not m.group(2)[0:1].isupper()
def s_infi_commencer_finir_par_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_verbe_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:cesser|décider|défendre|suggérer|commander|essayer|tenter|choisir|permettre|interdire) ", False) and analysex(m.group(2), ":(?:Q|2p)", ":M")
def s_infi_verbe_de_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_adjectifs_masculins_singuliers_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":N.*:m:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":Y", ">aller |:(?:M|N.*:m:s)") and isNextVerb(dDA, s[m.end():], m.end())
def s_infi_adjectifs_masculins_singuliers_1 (s, m):
    return suggVerbPpas(m.group(2), ":m:s")
def c_infi_adjectifs_féminins_singuliers_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":N.*:f:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":Y", ">aller |:M") and isNextVerb(dDA, s[m.end():], m.end())
def s_infi_adjectifs_féminins_singuliers_1 (s, m):
    return suggVerbPpas(m.group(2), ":f:s")
def c_infi_adjectifs_singuliers_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":N.*:[si]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":Y", ">aller |:M") and isNextVerb(dDA, s[m.end():], m.end())
def s_infi_adjectifs_singuliers_1 (s, m):
    return suggVerbPpas(m.group(2), ":s")
def c_infi_adjectifs_pluriels_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":N.*:[pi]", ":G") and morphex(dDA, (m.start(2), m.group(2)), ":Y", ">aller |:M") and isNextVerb(dDA, s[m.end():], m.end())
def s_infi_adjectifs_pluriels_1 (s, m):
    return suggVerbPpas(m.group(2), ":p")
def c_conj_participe_présent_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":A", False)
def s_conj_participe_présent_1 (s, m):
    return m.group(1)[:-1]
def c_p_pas_point_rien_bien_ensemble1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False)
def c_p_que_semble_le_penser_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">sembler ", False)
def c_p_en_plein_xxx_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False) and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_de_vinfi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V[123]_i", ">(?:devenir|rester|demeurer) ") and isNextNotCOD(dDA, s[m.end():], m.end())
def c_p_de_manière_façon_xxx_et_xxx_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":A", False) and morphex(dDA, (m.start(2), m.group(2)), ":A", ":[GM]")
def c_p_de_manière_façon_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":A", False)
def c_p_de_nom_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:s", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[GV]") and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_det_nom_adj_nom_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":V0") and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ]", ":(?:G|[123][sp]|P)")
def c_p_groupes_déjà_simplifiés_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False) and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_y_compris_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:[jn]’|tu )$")
def c_p_préposition_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":[GY]") and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_préposition_déterminant_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":G") and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_lors_de_du_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":G") and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_nul_doute_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_p_douter_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">douter ", False) and look(s[:m.start()], r"(?i)\b(?:[mts]e|[nv]ous) +$")
def c_p_de_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":N", ":[GY]") and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_de_pronom_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ]", False) and isEndOfNG(dDA, s[m.end():], m.end())
def c_p_de_la_leur_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":Y") and isEndOfNG(dDA, s[m.end():], m.end())
def c_ocr_être_participes_passés_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def c_ocr_être_participes_passés_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).endswith("e") and morphex(dDA, (m.start(2), m.group(2)), ":V1.*:Ip.*:[13]s", ":(?:[GM]|A)") and not look(s[:m.start()], r"(?i)\belle +(?:ne +|n’|)$")
def s_ocr_être_participes_passés_2 (s, m):
    return suggVerbPpas(m.group(2), ":m:s")
def c_ocr_être_participes_passés_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(2).endswith("s") and morphex(dDA, (m.start(2), m.group(2)), ":V1.*:Ip.*:2s", ":(?:[GM]|A)") and not look(s[:m.start()], r"(?i)\belles +(?:ne +|n’|)$")
def s_ocr_être_participes_passés_3 (s, m):
    return suggVerbPpas(m.group(2), ":m:p")
def c_ocr_avoir_participes_passés_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False)
def c_ocr_avoir_participes_passés_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2).endswith("e") and morphex(dDA, (m.start(2), m.group(2)), ":V1.*:Ip.*:[13]s", ":[GM]|>envie ")
def s_ocr_avoir_participes_passés_2 (s, m):
    return suggVerbPpas(m.group(2), ":m:s")
def c_ocr_avoir_participes_passés_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(2).endswith("s") and morphex(dDA, (m.start(2), m.group(2)), ":V1.*:Ip.*:2s", ":[GM]")
def s_ocr_avoir_participes_passés_3 (s, m):
    return suggVerbPpas(m.group(2), ":m:p")
def c_conf_c_en_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return re.search("(?i)^(?:fini|terminé)s?", m.group(2)) and morph(dDA, prevword1(s, m.start()), ":C", False, True)
def c_conf_c_en_être_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return re.search("(?i)^(?:assez|trop)$", m.group(2)) and (look(s[m.end():], "^ +d(?:e |’)") or look(s[m.end():], "^ *$|^,"))
def c_conf_c_en_être_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":A", ":[GVW]") and morph(dDA, prevword1(s, m.start()), ":C", False, True)
def c_conf_aller_de_soi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">aller", False) and not look(s[m.end():], " soit ")
def c_sgpl_verbe_fort_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":[AN].*:[me]:[pi]|>(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre|appara[îi]tre) .*:(?:[123]p|P|Q)|>(?:affirmer|trouver|croire|désirer|estime|préférer|penser|imaginer|voir|vouloir|aimer|adorer|souhaiter) ") and not morph(dDA, nextword1(s, m.end()), ":A.*:[me]:[pi]", False)
def c_sgpl_bien_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, prevword1(s, m.start()), ":V", ":D.*:p|:A.*:p", False)
def c_infi_d_en_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False)
def s_infi_d_en_y_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_de_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False)
def s_infi_de_pronom_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_de_pronom_le_les_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False)
def s_infi_de_pronom_le_les_la_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_faire_vouloir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:faire|vouloir) ", False) and not look(s[:m.start()], r"(?i)\b(?:en|[mtsld]es?|[nv]ous|un) +$") and morphex(dDA, (m.start(2), m.group(2)), ":V", ":M") and not (re.search("(?i)^(?:fait|vouloir)$", m.group(1)) and m.group(2).endswith("é")) and not (re.search("(?i)^(?:fait|vouloir)s$", m.group(1)) and m.group(2).endswith("és"))
def s_infi_faire_vouloir_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_me_te_se_faire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">faire ", False) and morphex(dDA, (m.start(2), m.group(2)), ":V", ":M")
def s_infi_me_te_se_faire_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_de_vouloir_faire_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":M")
def s_infi_de_vouloir_faire_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_savoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">savoir :V", False) and morph(dDA, (m.start(2), m.group(2)), ":V", False) and not look(s[:m.start()], r"(?i)\b(?:[mts]e|[vn]ous|les?|la|un) +$")
def s_infi_savoir_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_il_faut_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Q|2p)", False)
def s_infi_il_faut_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_il_faut_le_les_la_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:Q|2p)", ":N")
def s_infi_il_faut_le_les_la_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_lui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":Q", False)
def s_infi_lui_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_conj_se_conf_être_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">avoir ", False)
def c_conj_se_conf_être_avoir_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":3p", False)
def c_conj_se_conf_être_avoir_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def c_conj_je_me_conf_être_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False)
def c_conj_tu_te_conf_être_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and not morph(dDA, prevword1(s, m.start()), ":V0", False, False)
def c_conj_nous_nous_conf_être_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">avoir ", False) and look(s[:m.start()], "^ *$|, *$")
def c_conj_nous_nous_conf_être_avoir_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_conj_vous_vous_conf_être_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">avoir ", False) and look(s[:m.start()], "^ *$|, *$")
def c_conj_vous_vous_conf_être_avoir_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_ppas_je_me_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:p", ":(?:G|Q.*:[si])") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not look(s[:m.start()], r"\b[qQ]ue? +$")) )
def s_ppas_je_me_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":m:s")
def c_ppas_tu_te_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:p", ":(?:G|Q.*:[si])") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not look(s[:m.start()], r"\b[qQ]ue? +$")) )
def s_ppas_tu_te_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":m:s")
def c_ppas_il_se_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:(?:f|m:p)", ":(?:G|Q.*:m:[si])|>dire ") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not look(s[:m.start()], r"\b[qQ]ue? +$")) )
def s_ppas_il_se_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":m:s")
def c_ppas_elle_se_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:(?:m|f:p)", ":(?:G|Q.*:f:[si])|>dire ") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not morph(dDA, prevword1(s, m.start()), ":R|>que ", False, False)) )
def s_ppas_elle_se_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":f:s")
def c_ppas_nous_nous_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:s", ":(?:G|Q.*:[pi])|>dire ") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not morph(dDA, prevword1(s, m.start()), ":R|>que ", False, False)) )
def s_ppas_nous_nous_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":p")
def c_ppas_ils_se_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:(?:f|m:s)", ":(?:G|Q.*:m:[pi])|>dire ") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not look(s[:m.start()], r"\b[qQ]ue? +$")) )
def s_ppas_ils_se_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":m:p")
def c_ppas_elles_se_être_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":Q.*:(?:m|f:s)", ":(?:G|Q.*:f:[pi])|>dire ") and ( morph(dDA, (m.start(1), m.group(1)), ":V[123]_.__p_e_") or (look(s[m.end():], "^ *$") and not morph(dDA, prevword1(s, m.start()), ":R|>que ", False, False)) )
def s_ppas_elles_se_être_verbe_1 (s, m):
    return suggVerbPpas(m.group(1), ":f:p")
def c_ppas_se_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">être ", False)
def c_ppas_se_être_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:Y|[123][sp])", ":Q") and not re.search(r"(?i)^t’(?:es|étais)", m.group(0))
def s_ppas_se_être_2 (s, m):
    return suggVerbPpas(m.group(2))
def c_ppas_se_être_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(1), m.group(1)), ":[123]s", False) and morph(dDA, (m.start(2), m.group(2)), ":Q.*:p", False) and not look(s[:m.start()], r"(?i)\bque?[, ]|\bon (?:ne |)$") and not re.search(r"(?i)^t’(?:es|étais)", m.group(0))
def s_ppas_se_être_3 (s, m):
    return suggSing(m.group(2))
def c_ppas_me_te_laisser_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">laisser ", False) and  morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:p", ":(?:[YG]|[AQ].*:[is])")
def s_ppas_me_te_laisser_adj_1 (s, m):
    return suggSing(m.group(3))
def c_ppas_nous_les_laisser_adj_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">laisser ", False) and morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:s", ":(?:[YG]|[AQ].*:[ip])") and (m.group(1).endswith("es") or ( m.group(1).endswith("us") and not m.group(2).endswith("ons") ))
def s_ppas_nous_les_laisser_adj_1 (s, m):
    return suggPlur(m.group(3))
def c_ppas_je_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(1), m.group(1)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(1).endswith(" été")) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWYsi]")
def s_ppas_je_verbe_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_tu_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(1), m.group(1)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(1).endswith(" été")) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWYsi]")
def s_ppas_tu_verbe_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_il_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]"))
def s_ppas_il_verbe_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_c_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (morph(dDA, (m.start(1), m.group(1)), ">seule ", False) and look(s[m.end():], "^ +que? ")) and ( morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p", ":[GWYsi]") or ( morphex(dDA, (m.start(1), m.group(1)), ":[AQ].*:f", ":[GWYme]") and not morph(dDA, nextword1(s, m.end()), ":N.*:f", False, False) ) )
def s_ppas_c_être_1 (s, m):
    return suggMasSing(m.group(1))
def c_ppas_ç_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ].*:p", ":[GWYsi]") or ( morphex(dDA, (m.start(1), m.group(1)), ":[AQ].*:f", ":[GWYme]") and not morph(dDA, nextword1(s, m.end()), ":N.*:f", False, False) )
def s_ppas_ç_être_1 (s, m):
    return suggMasSing(m.group(1))
def c_ppas_ça_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or ( morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]") and not morph(dDA, nextword1(s, m.end()), ":N.*:f", False, False) ) ) and not morph(dDA, prevword1(s, m.start()), ":(?:R|V...t)", False, False)
def s_ppas_ça_verbe_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_lequel_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and ( morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or ( morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]") and not morph(dDA, nextword1(s, m.end()), ":N.*:f", False, False) ) ) and not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def s_ppas_lequel_verbe_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_elle_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWYfe]")) and not morph(dDA, prevword1(s, m.start()), ":R|>de ", False, False)
def s_ppas_elle_verbe_1 (s, m):
    return suggFemSing(m.group(3))
def c_ppas_elle_qui_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWYfe]"))
def s_ppas_elle_qui_verbe_1 (s, m):
    return suggFemSing(m.group(3))
def c_ppas_nous_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(2)) and not look(s[:m.start()], r"(?i)\b(?:nous|ne) +$") and ((morph(dDA, (m.start(1), m.group(1)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) and morph(dDA, (m.start(1), m.group(1)), ":1p", False)) or m.group(1).endswith(" été")) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[GWYpi]")
def s_ppas_nous_verbe_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_ils_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(3)) and (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[GWYpi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]")) and not look(s[:m.start()], "(?i)ce que? +$") and (not re.search("^(?:ceux-(?:ci|là)|lesquels)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_ils_verbe_1 (s, m):
    return suggMasPlur(m.group(3))
def c_ppas_elles_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(3)) and (morph(dDA, (m.start(2), m.group(2)), ">(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre) ", False) or m.group(2).endswith(" été")) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[GWYpi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWYfe]")) and (not re.search("(?i)^(?:elles|celles-(?:ci|là)|lesquelles)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_elles_verbe_1 (s, m):
    return suggFemPlur(m.group(3))
def c_ppas_avoir_été_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0a", False)
def c_ppas_avoir_été_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":[123]s", ":[GNAQWY]")
def s_ppas_avoir_été_2 (s, m):
    return suggVerbPpas(m.group(3))
def c_ppas_avoir_été_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], "[çcCÇ]’$|[cC]e n’$|[çÇ]a (?:n’|)$") and not look(s[:m.start()], "(?i)^ *ne pas ") and not morph(dDA, prevword1(s, m.start()), ":Y", False)
def c_ppas_avoir_été_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":Y", ":A")
def c_ppas_avoir_été_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(3), m.group(3)), ":V1..t.*:Y", ":A")
def s_ppas_avoir_été_5 (s, m):
    return suggVerbPpas(m.group(3))
def c_ppas_je_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWYsi]")
def s_ppas_je_verbe_être_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_tu_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWYsi]")
def s_ppas_tu_verbe_être_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_il_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]"))
def s_ppas_il_verbe_être_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_ça_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[MWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]")) and not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def s_ppas_ça_verbe_être_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_elle_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWYfe]")) and not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def s_ppas_elle_verbe_être_1 (s, m):
    return suggFemSing(m.group(3))
def c_ppas_elle_qui_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[MWYsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWYfe]"))
def s_ppas_elle_qui_verbe_être_1 (s, m):
    return suggFemSing(m.group(3))
def c_ppas_nous_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(2)) and morph(dDA, (m.start(1), m.group(1)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and morph(dDA, (m.start(1), m.group(1)), ":1p", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[GWYpi]")
def s_ppas_nous_verbe_être_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_ils_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(3)) and morph(dDA, (m.start(2), m.group(2)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[GWYpi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWYme]")) and (not re.search("^(?:ceux-(?:ci|là)|lesquels)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_ils_verbe_être_1 (s, m):
    return suggMasPlur(m.group(3))
def c_ppas_elles_verbe_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(3)) and morph(dDA, (m.start(2), m.group(2)), ">(?:sembler|para[îi]tre|pouvoir|penser|préférer|croire|d(?:evoir|éclarer|ésirer|étester|ire)|vouloir|affirmer|aimer|adorer|souhaiter|estimer|imaginer|risquer|aller) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[GWYpi]") or morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWYfe]")) and (not re.search("^(?:elles|celles-(?:ci|là)|lesquelles)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_elles_verbe_être_1 (s, m):
    return suggFemPlur(m.group(3))
def c_ppas_être_accord_singulier_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GMWYsi]") and not morph(dDA, (m.start(1), m.group(1)), ":G", False)
def s_ppas_être_accord_singulier_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_être_accord_pluriel_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(2)) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[GWYpi]") and not morph(dDA, (m.start(1), m.group(1)), ":G", False)
def s_ppas_être_accord_pluriel_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_sujet_être_accord_genre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(3)) and ((morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:f", ":[GWme]") and morphex(dDA, (m.start(2), m.group(2)), ":m", ":[Gfe]")) or (morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:m", ":[GWfe]") and morphex(dDA, (m.start(2), m.group(2)), ":f", ":[Gme]"))) and not ( morph(dDA, (m.start(3), m.group(3)), ":p", False) and morph(dDA, (m.start(2), m.group(2)), ":s", False) ) and not morph(dDA, prevword1(s, m.start()), ":(?:R|P|Q|Y|[123][sp])", False, False) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_ppas_sujet_être_accord_genre_1 (s, m):
    return switchGender(m.group(3))
def c_ppas_nom_propre_être_accord_genre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(2)) and ((morphex(dDA, (m.start(1), m.group(1)), ":M[1P].*:f", ":[GWme]") and morphex(dDA, (m.start(2), m.group(2)), ":m", ":[GWfe]")) or (morphex(dDA, (m.start(1), m.group(1)), ":M[1P].*:m", ":[GWfe]") and morphex(dDA, (m.start(2), m.group(2)), ":f", ":[GWme]"))) and not morph(dDA, prevword1(s, m.start()), ":(?:R|P|Q|Y|[123][sp])", False, False) and not look(s[:m.start()], r"\b(?:et|ou|de) +$")
def s_ppas_nom_propre_être_accord_genre_1 (s, m):
    return switchGender(m.group(2))
def c_ppas_adj_accord_je_tu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":A.*:p", ":(?:G|E|M1|W|s|i)")
def s_ppas_adj_accord_je_tu_1 (s, m):
    return suggSing(m.group(1))
def c_ppas_adj_accord_il_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":A.*:[fp]", ":(?:G|E|M1|W|m:[si])")
def s_ppas_adj_accord_il_1 (s, m):
    return suggMasSing(m.group(1))
def c_ppas_adj_accord_elle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":A.*:[mp]", ":(?:G|E|M1|W|f:[si])|>(?:désoler|pire) ")
def s_ppas_adj_accord_elle_1 (s, m):
    return suggFemSing(m.group(1))
def c_ppas_adj_accord_ils_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":A.*:[fs]", ":(?:G|E|M1|W|m:[pi])|>(?:désoler|pire) ")
def s_ppas_adj_accord_ils_1 (s, m):
    return suggMasPlur(m.group(1))
def c_ppas_adj_accord_elles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":A.*:[ms]", ":(?:G|E|M1|W|f:[pi])|>(?:désoler|pire) ")
def s_ppas_adj_accord_elles_1 (s, m):
    return suggFemPlur(m.group(1))
def c_ppas_être_rendu_compte_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), "V0e", False) and m.group(3) != "rendu"
def c_ppas_inversion_être_je_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y|[NAQ].*:p)", ":[GWsi]")
def s_ppas_inversion_être_je_1 (s, m):
    return suggSing(m.group(1))
def c_ppas_inversion_être_tu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y|[NAQ].*:p)", ":[GWsi]")
def s_ppas_inversion_être_tu_1 (s, m):
    return suggSing(m.group(1))
def c_ppas_inversion_être_il_ce_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|Y|[NAQ].*:[pf])", ":(?:G|W|[me]:[si])|question ") and not (m.group(1) == "ce" and morph(dDA, (m.start(2), m.group(2)), ":Y", False))
def s_ppas_inversion_être_il_ce_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_inversion_être_elle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y|[NAQ].*:[pm])", ":(?:G|W|[fe]:[si])")
def s_ppas_inversion_être_elle_1 (s, m):
    return suggFemSing(m.group(1))
def c_ppas_inversion_être_nous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y|[NAQ].*:s)", ":[GWpi]|>dire ")
def s_ppas_inversion_être_nous_1 (s, m):
    return suggPlur(m.group(1))
def c_ppas_inversion_être_ils_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(1)) and (morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y|[NAQ].*:s)", ":[GWpi]|>dire ") or morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|[AQ].*:f)", ":[GWme]|>dire "))
def s_ppas_inversion_être_ils_1 (s, m):
    return suggMasPlur(m.group(1))
def c_ppas_inversion_être_elles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^légion$", m.group(1)) and (morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|Y|[NAQ].*:s)", ":[GWpi]|>dire ") or morphex(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|[AQ].*:m)", ":[GWfe]|>dire "))
def s_ppas_inversion_être_elles_1 (s, m):
    return suggFemPlur(m.group(1))
def c_ppas_sont_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":[QWGBMpi]") and not re.search("(?i)^(?:légion|nombre|cause)$", m.group(1)) and not look(s[:m.start()], r"(?i)\bce que?\b")
def s_ppas_sont_1 (s, m):
    return suggPlur(m.group(1))
def c_ppas_sont_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:N|A|Q|W|G|3p)") and not look(s[:m.start()], r"(?i)\bce que?\b")
def s_ppas_sont_2 (s, m):
    return suggVerbPpas(m.group(1), ":m:p")
def c_ppas_je_me_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWYsi]")
def s_ppas_je_me_verbe_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_tu_te_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:p", ":[GWYsi]")
def s_ppas_tu_te_verbe_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_il_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f", ":[GWYme]")) and (not re.search("^(?:celui-(?:ci|là)|lequel)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_il_se_verbe_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_elle_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":[GWYfe]")) and not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def s_ppas_elle_se_verbe_1 (s, m):
    return suggFemSing(m.group(3))
def c_ppas_elle_qui_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:p", ":[GWsi]") or morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":[GWYfe]"))
def s_ppas_elle_qui_se_verbe_1 (s, m):
    return suggFemSing(m.group(3))
def c_ppas_nous_nous_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:s", ":[GWpi]")
def s_ppas_nous_nous_verbe_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_ils_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[GWpi]") or morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:f", ":[GWYme]")) and (not re.search("^(?:ceux-(?:ci|là)|lesquels)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_ils_se_verbe_1 (s, m):
    return suggMasPlur(m.group(3))
def c_ppas_elles_se_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:montrer|penser|révéler|savoir|sentir|voir|vouloir) ", False) and (morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:s", ":[GWpi]") or morphex(dDA, (m.start(3), m.group(3)), ":[NAQ].*:m", ":[GWYfe]")) and (not re.search("^(?:elles|celles-(?:ci|là)|lesquelles)$", m.group(1)) or not morph(dDA, prevword1(s, m.start()), ":R", False, False))
def s_ppas_elles_se_verbe_1 (s, m):
    return suggFemPlur(m.group(3))
def c_ppas_le_verbe_pensée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire|rendre|voilà) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[AQ].*:(?:[me]:p|f)", ":(?:G|Y|[AQ].*:m:[is])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_le_verbe_pensée_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_la_verbe_pensée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire|rendre|voilà) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[AQ].*:(?:[fe]:p|m)", ":(?:G|Y|[AQ]:f:[is])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_la_verbe_pensée_1 (s, m):
    return suggFemSing(m.group(2))
def c_ppas_les_verbe_pensée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire|rendre|voilà) ", False) and morphex(dDA, (m.start(2), m.group(2)), ":[AQ].*:s", ":(?:G|Y|[AQ].*:[ip])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_les_verbe_pensée_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_me_te_verbe_pensée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">(?:trouver|considérer|croire|rendre|voilà) ", False) and morphex(dDA, (m.start(3), m.group(3)), ":[AQ].*:p", ":(?:G|Y|[AQ].*:[is])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_me_te_verbe_pensée_1 (s, m):
    return suggSing(m.group(3))
def c_ppas_se_verbe_pensée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire|rendre) .*:3s", False) and morphex(dDA, (m.start(2), m.group(2)), ":[AQ].*:p", ":(?:G|Y|[AQ].*:[is])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_se_verbe_pensée_1 (s, m):
    return suggSing(m.group(2))
def c_ppas_se_verbe_pensée_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morph(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire|rendre) .*:3p", False) and morphex(dDA, (m.start(2), m.group(2)), ":[AQ].*:s", ":(?:G|Y|[AQ].*:[ip])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_se_verbe_pensée_2 (s, m):
    return suggPlur(m.group(2))
def c_ppas_nous_verbe_pensée_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return ( morphex(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire|rendre|voilà) ", ":1p") or (morph(dDA, (m.start(1), m.group(1)), ">(?:trouver|considérer|croire) .*:1p", False) and look(s[:m.start()], r"\bn(?:ous|e) +$")) ) and morphex(dDA, (m.start(2), m.group(2)), ":[AQ].*:s", ":(?:G|Y|[AQ].*:[ip])") and not (morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":3s", False))
def s_ppas_nous_verbe_pensée_1 (s, m):
    return suggPlur(m.group(2))
def c_p_les_avoir_fait_vinfi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and morph(dDA, (m.start(3), m.group(3)), ":Y", False)
def c_ppas_pronom_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:barre|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours)$", m.group(2)) and morph(dDA, prevword1(s, m.start()), ">(?:comme|et|lorsque?|mais|o[uù]|puisque?|qu(?:oique?|i|and)|si(?:non|)) ", False, True) and morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and not m.group(2).isupper() and morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|Q.*:[fp])", ":(?:G|W|Q.*:m:[si])")
def s_ppas_pronom_avoir_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_nous_vous_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":Os", False) and not re.search("(?i)^(?:barre|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours)$", m.group(3)) and morph(dDA, prevword1(s, m.start()), ">(?:comme|et|lorsque?|mais|o[uù]|puisque?|qu(?:oique?|i|and)|si(?:non|)) ", False, True) and morph(dDA, (m.start(2), m.group(2)), ":V0a", False) and not m.group(3).isupper() and morphex(dDA, (m.start(3), m.group(3)), ":(?:[123][sp]|Q.*:[fp])", ":(?:G|W|Q.*:m:[si])")
def s_ppas_nous_vous_avoir_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_det_nom_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:barre|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours)$", m.group(4)) and morph(dDA, prevword1(s, m.start()), ">(?:comme|et|lorsque?|mais|o[uù]|puisque?|qu(?:oique?|i|and)|si(?:non|)) ", False, True) and not morph(dDA, (m.start(2), m.group(2)), ":G", False) and morph(dDA, (m.start(3), m.group(3)), ":V0a", False) and not m.group(4).isupper() and morphex(dDA, (m.start(4), m.group(4)), ":(?:[123][sp]|Q.*:[fp])", ":(?:G|W|Q.*:m:[si])") and not (m.group(3) == "avions" and morph(dDA, (m.start(4), m.group(4)), ":3[sp]", False))
def s_ppas_det_nom_avoir_1 (s, m):
    return suggMasSing(m.group(4))
def c_ppas_les_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morphex(dDA, (m.start(2), m.group(2)), ":V[0-3]..t.*:Q.*:s", ":[GWpi]")
def s_ppas_les_avoir_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_nous_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[m.end():], "^ *$") and morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morphex(dDA, (m.start(2), m.group(2)), ":V[0-3]..t_.*:Q.*:s", ":[GWpi]") and morphex(dDA, prevword1(s, m.start()), ":(?:M|Os|N)", ":R") and not look(s[:m.start()], r"\bque? +\w[\w-]+ +$")
def s_ppas_nous_avoir_1 (s, m):
    return suggPlur(m.group(2))
def c_ppas_l_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morphex(dDA, (m.start(2), m.group(2)), ":V[0-3]..t.*:Q.*:p", ":[GWsi]")
def s_ppas_l_avoir_1 (s, m):
    return m.group(2)[:-1]
def c_ppas_m_t_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0a", False) and morphex(dDA, (m.start(3), m.group(3)), ":V[0-3]..t_.*:Q.*:p", ":[GWsi]") and not look(s[:m.start()], r"\bque? ")
def s_ppas_m_t_avoir_1 (s, m):
    return m.group(3)[:-1]
def c_ppas_qui_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and morphex(dDA, (m.start(2), m.group(2)), ":Q.*:(?:f|m:p)", ":m:[si]")
def s_ppas_qui_avoir_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_avoir_ppas_mas_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("(?i)^(?:confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours)$", m.group(1)) and morphex(dDA, (m.start(1), m.group(1)), ":Q.*:(?:f|m:p)", ":m:[si]") and look(s[:m.start()], "(?i)(?:après +$|sans +$|pour +$|que? +$|quand +$|, +$|^ *$)")
def s_ppas_avoir_ppas_mas_sing_1 (s, m):
    return suggMasSing(m.group(1))
def c_ppas_m_t_l_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and morphex(dDA, (m.start(2), m.group(2)), ":(?:Y|[123][sp])", ":[QGWMX]") and not re.search(r"(?i)^t’as +envie", m.group(0))
def s_ppas_m_t_l_avoir_1 (s, m):
    return suggVerbPpas(m.group(2), ":m:s")
def c_ppas_det_plur_COD_que_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(3), m.group(3)), ":V0a", False) and not ((re.search("^(?:décidé|essayé|tenté|oublié)$", m.group(4)) and look(s[m.end():], " +d(?:e |’)")) or (re.search("^réussi$", m.group(4)) and look(s[m.end():], " +à"))) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ]", False) and morphex(dDA, (m.start(4), m.group(4)), ":V[0-3]..t.*:Q.*:s", ":[GWpi]") and not morph(dDA, nextword1(s, m.end()), ":(?:Y|Oo|D)", False)
def s_ppas_det_plur_COD_que_avoir_1 (s, m):
    return suggPlur(m.group(4), m.group(2))
def c_ppas_det_mas_sing_COD_que_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(3), m.group(3)), ":V0a", False) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:m", False) and (morphex(dDA, (m.start(4), m.group(4)), ":V[0-3]..t.*:Q.*:f", ":[GWme]") or morphex(dDA, (m.start(4), m.group(4)), ":V[0-3]..t.*:Q.*:p", ":[GWsi]"))
def s_ppas_det_mas_sing_COD_que_avoir_1 (s, m):
    return suggMasSing(m.group(4))
def c_ppas_det_fem_sing_COD_que_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(3), m.group(3)), ":V0a", False) and not ((re.search("^(?:décidé|essayé|tenté)$", m.group(4)) and look(s[m.end():], " +d(?:e |’)")) or (re.search("^réussi$", m.group(4)) and look(s[m.end():], " +à"))) and morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:f", False) and (morphex(dDA, (m.start(4), m.group(4)), ":V[0-3]..t.*:Q.*:m", ":[GWfe]") or morphex(dDA, (m.start(4), m.group(4)), ":V[0-3]..t.*:Q.*:p", ":[GWsi]")) and not morph(dDA, nextword1(s, m.end()), ":(?:Y|Oo)|>que?", False)
def s_ppas_det_fem_sing_COD_que_avoir_1 (s, m):
    return suggFemSing(m.group(4))
def c_ppas_ce_que_pronom_avoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and (morphex(dDA, (m.start(2), m.group(2)), ":V[0-3]..t.*:Q.*:f", ":[GWme]") or morphex(dDA, (m.start(2), m.group(2)), ":V[0-3]..t.*:Q.*:p", ":[GWsi]"))
def s_ppas_ce_que_pronom_avoir_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_avoir_conf_infi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not re.search("^(?:A|avions)$", m.group(1)) and morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morph(dDA, (m.start(2), m.group(2)), ":V.+:(?:Y|2p)", False)
def s_ppas_avoir_conf_infi_1 (s, m):
    return suggVerbPpas(m.group(2), ":m:s")
def c_ppas_avoir_conf_infi_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and m.group(1) == "a" and m.group(2).endswith("r") and not look(s[:m.start()], r"(?i)\b(?:[mtn]’|il +|on +|elle +)$")
def c_ppas_avoir_dû_vinfi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and (morph(dDA, (m.start(3), m.group(3)), ":Y") or re.search("^(?:[mtsn]e|[nv]ous|leur|lui)$", m.group(3)))
def c_ppas_avoir_pronom_du_vinfi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and (morph(dDA, (m.start(3), m.group(3)), ":Y") or re.search("^(?:[mtsn]e|[nv]ous|leur|lui)$", m.group(3)))
def c_ppas_ton_son_dû_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":[NAQ].*:[me]", False)
def c_ppas_qui_être_dû_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False)
def c_ppas_avoir_pronom1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morphex(dDA, (m.start(2), m.group(2)), ":(?:Y|2p|Q.*:[fp])", ":m:[si]") and m.group(2) != "prise" and not morph(dDA, prevword1(s, m.start()), ">(?:les|[nv]ous|en)|:[NAQ].*:[fp]", False) and not look(s[:m.start()], r"(?i)\b(?:quel(?:le|)s?|combien) ")
def s_ppas_avoir_pronom1_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_avoir_pronom2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morphex(dDA, (m.start(2), m.group(2)), ":(?:Y|2p|Q.*:[fp])", ":m:[si]") and m.group(2) != "prise" and not morph(dDA, prevword1(s, m.start()), ">(?:les|[nv]ous|en)|:[NAQ].*:[fp]", False) and not look(s[:m.start()], r"(?i)\b(?:quel(?:le|)s?|combien) ")
def s_ppas_avoir_pronom2_1 (s, m):
    return suggMasSing(m.group(2))
def c_ppas_l_m_t_avoir_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":V0a", False) and morphex(dDA, (m.start(3), m.group(3)), ":(?:Y|2p|Q.*:p)", ":[si]")
def s_ppas_l_m_t_avoir_pronom_1 (s, m):
    return suggMasSing(m.group(3))
def c_ppas_les_avoir_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0a", False) and morphex(dDA, (m.start(2), m.group(2)), ":V[123]..t.*:Q.*:s", ":[GWpi]")
def s_ppas_les_avoir_pronom_1 (s, m):
    return suggPlur(m.group(2))
def c_conj_nous_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:G|Y|P|1p|3[sp])") and not look(s[m.end():], "^ +(?:je|tu|ils?|elles?|on|[vn]ous) ")
def s_conj_nous_verbe_1 (s, m):
    return suggVerb(m.group(1), ":1p")
def c_conj_vous_verbe1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:G|Y|P|2p|3[sp])") and not look(s[m.end():], "^ +(?:je|ils?|elles?|on|[vn]ous) ")
def s_conj_vous_verbe1_1 (s, m):
    return suggVerb(m.group(1), ":2p")
def c_conj_vous_verbe2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":2p") and look(s[:m.start()], "^ *$|, *$")
def s_conj_vous_verbe2_1 (s, m):
    return suggVerb(m.group(1), ":2p")
def c_conj_se_incohérence_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":2s", ":3[sp]")
def s_conj_se_incohérence_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_se_incohérence_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(1), m.group(1)), ":1p", ":3[sp]")
def s_conj_se_incohérence_2 (s, m):
    return suggVerb(m.group(1), ":3p")
def c_conj_se_incohérence_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and morphex(dDA, (m.start(1), m.group(1)), ":2p", ":3[sp]")
def s_conj_se_incohérence_3 (s, m):
    return suggVerbInfi(m.group(1))
def c_conf_det_nom_où_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[NAQ]", ":G")
def c_p_premier_ne_pro_per_obj1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj1_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj2_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj2_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":X|>rien ", False)
def c_p_premier_ne_pro_per_obj3_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj3_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj4_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj4_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj5_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj5_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj5_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":X|>rien ", False)
def c_p_premier_ne_pro_per_obj6_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj6_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj7_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P)", False)
def d_p_premier_ne_pro_per_obj7_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2),":(?:[123][sp]|P)")
def c_p_premier_ne_pro_per_obj7_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":X|>rien ", False)
def c_imp_confusion_2e_pers_pluriel_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False) and look(s[:m.start()], "^ *$|, *$")
def c_imp_confusion_2e_pers_pluriel_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "moi"
def s_imp_confusion_2e_pers_pluriel_2 (s, m):
    return suggVerbTense(m.group(1), ":E", ":2p") + "-moi"
def c_imp_confusion_2e_pers_pluriel_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(2).startswith("l") and morph(dDA, nextword1(s, m.end()), ":[OR]", ":N", True)
def s_imp_confusion_2e_pers_pluriel_3 (s, m):
    return suggVerbTense(m.group(1), ":E", ":2p") + "-" + m.group(2)
def c_imp_confusion_2e_pers_pluriel_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and look(s[m.end():], "^ *$|^,")
def s_imp_confusion_2e_pers_pluriel_4 (s, m):
    return suggVerbTense(m.group(1), ":E", ":2p") + "-" + m.group(2)
def c_imp_vgroupe1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V[13].*:Ip.*:2s", ":[GNAM]")
def s_imp_vgroupe1_1 (s, m):
    return m.group(1)[:-1]
def c_imp_allez2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[MYOs]")
def c_imp_vgroupe2_vgroupe3_t_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V[23].*:Ip.*:3s", ":[GNA]|>(?:devoir|suffire)") and analyse(m.group(1)[:-1]+"s", ":E:2s", False) and not (re.search("(?i)^vient$", m.group(1)) and look(s[m.end():], "^ +(?:l[ea]|se |s’)")) and not (re.search("(?i)^dit$", m.group(1)) and look(s[m.end():], "^ +[A-ZÉÈÂÎ]"))
def s_imp_vgroupe2_vgroupe3_t_1 (s, m):
    return m.group(1)[:-1]+"s"
def c_imp_vgroupe3_d_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V3.*:Ip.*:3s", ":[GNA]") and not (re.search("(?i)^répond$", m.group(1)) and look(s[m.end():], "^ +[A-ZÉÈÂÎ]"))
def c_imp_sois_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V") or (morphex(dDA, (m.start(2), m.group(2)), ":A", ":G") and not look(s[m.end():], r"\bsoit\b"))
def c_imp_verbe_lui_le_la_les_leur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":E|>chez", False) and _oSpellChecker.isValid(m.group(1))
def s_imp_verbe_lui_le_la_les_leur_1 (s, m):
    return suggVerbImpe(m.group(1))
def c_imp_verbe_lui_le_la_les_leur_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "leurs"
def c_imp_verbe_moi_toi_m_t_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":E|>chez", False) and _oSpellChecker.isValid(m.group(1))
def s_imp_verbe_moi_toi_m_t_en_1 (s, m):
    return suggVerbTense(m.group(1), ":E", ":2s")
def c_imp_union_moi_toi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":E", ":[GM]")
def c_imp_union_nous_vous_lui_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":E", ":[GM]") and morphex(dDA, nextword1(s, m.end()), ":", ":(?:Y|3[sp])", True) and morph(dDA, prevword1(s, m.start()), ":Cc", False, True)
def c_imp_union_les_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":E", ":[GM]") and morphex(dDA, nextword1(s, m.end()), ":", ":(?:N|A|Q|Y|B|3[sp])", True) and morph(dDA, prevword1(s, m.start()), ":Cc", False, True)
def c_imp_union_le_la_leur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":E", ":[GM]") and morphex(dDA, nextword1(s, m.end()), ":", ":(?:N|A|Q|Y|MP|H|T)", True) and morph(dDA, prevword1(s, m.start()), ":Cc", False, True)
def c_imp_laisser_le_la_les_infi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ">laisser ", False) and morphex(dDA, (m.start(3), m.group(3)), ":(?:Y|X|Oo)", ":[NAB]")
def s_imp_laisser_le_la_les_infi_1 (s, m):
    return m.group(1).replace(" ", "-")
def c_imp_apostrophe_m_t_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (m.group(0).endswith("t-en") and look(s[:m.start()], r"(?i)\bva$") and morph(dDA, nextword1(s, m.end()), ">guerre ", False, False))
def c_imp_union_m_t_en_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":E", ":(?:G|M[12])") and morphex(dDA, nextword1(s, m.end()), ":", ":(?:Y|[123][sp])", True)
def s_imp_union_m_t_en_y_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_imp_union_verbe_pronom_moi_toi_lui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":E", False)
def s_imp_union_verbe_pronom_moi_toi_lui_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_imp_union_verbe_pronom_en_y_leur_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":E", False) and morphex(dDA, nextword1(s, m.end()), ":[RC]", ":[NAQ]", True)
def s_imp_union_verbe_pronom_en_y_leur_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_imp_union_verbe_pronom_nous_vous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":E", False) and morphex(dDA, nextword1(s, m.end()), ":[RC]", ":Y", True)
def s_imp_union_verbe_pronom_nous_vous_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_imp_union_aller_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, nextword1(s, m.end()), ":Y", False, False)
def s_imp_union_aller_y_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_imp_union_vas_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and not morph(dDA, nextword1(s, m.end()), ":Y", False, False)
def s_imp_union_convenir_en_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_p_pro_per_obj01_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj01_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj02_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj02_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj03_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj03_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj04_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj04_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj05_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj05_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj06_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":R", False, True)
def c_p_pro_per_obj06_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj06_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj07_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def c_p_pro_per_obj07_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj07_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj08_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj08_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj08_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_p_pro_per_obj09_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return (m.group(1) == "le" and not morph(dDA, (m.start(2), m.group(2)), ":N.*:[me]:[si]")) or (m.group(1) == "la" and not morph(dDA, (m.start(2), m.group(2)), ":N.*:[fe]:[si]")) or (m.group(1) == "les" and not morph(dDA, (m.start(2), m.group(2)), ":N.*:.:[pi]"))
def c_p_pro_per_obj09_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj09_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj10_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def c_p_pro_per_obj10_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj10_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj11_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj11_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj11_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_p_pro_per_obj12_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj13_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":[123]s", False, False)
def c_p_pro_per_obj13_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj13_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj14_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":(?:[123]s|R)", False, False)
def c_p_pro_per_obj14_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj14_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj15_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":(?:[123]p|R)", False, False)
def c_p_pro_per_obj15_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj15_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj16_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, prevword1(s, m.start()), ":3p", False, False)
def c_p_pro_per_obj16_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj16_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj17_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def c_p_pro_per_obj17_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def d_p_pro_per_obj17_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj18_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", ":(?:[NAQ].*:[me]:[si]|G|M)")
def c_p_pro_per_obj18_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def d_p_pro_per_obj18_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj19_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", ":(?:[NAQ].*:[fe]:[si]|G|M)")
def c_p_pro_per_obj19_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def d_p_pro_per_obj19_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj20_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", ":(?:[NAQ].*:[si]|G|M)")
def c_p_pro_per_obj20_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def d_p_pro_per_obj20_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj21_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", ":(?:[NAQ].*:[si]|G|M)")
def c_p_pro_per_obj21_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def d_p_pro_per_obj21_2 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def d_p_pro_per_obj22_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":V")
def c_p_pro_per_obj23_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", ":(?:A|G|M|1p)")
def d_p_pro_per_obj23_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj23_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_p_pro_per_obj24_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", ":(?:A|G|M|2p)")
def d_p_pro_per_obj24_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj24_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_p_pro_per_obj25_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj25_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj26_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj26_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj26_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_p_pro_per_obj27_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj27_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj27_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_p_pro_per_obj28_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj28_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj28_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_p_pro_per_obj29_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj29_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj29_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":2s", False) or look(s[:m.start()], r"(?i)\b(?:je|tu|on|ils?|elles?|nous) +$")
def c_p_pro_per_obj30_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj30_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj30_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":2s|>(ils?|elles?|on) ", False) or look(s[:m.start()], r"(?i)\b(?:je|tu|on|ils?|elles?|nous) +$")
def c_p_pro_per_obj31_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj31_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj32_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj32_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj33_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj33_1 (s, m, dDA):
    return select(dDA, m.start(1), m.group(1), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj34_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":(?:[123][sp]|P|Y)", False)
def d_p_pro_per_obj34_1 (s, m, dDA):
    return select(dDA, m.start(2), m.group(2), ":(?:[123][sp]|P|Y)")
def c_p_pro_per_obj34_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_conf_pronom_verbe_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False) and m.group(2) != "A"
def c_conf_j_verbe_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V", False) and m.group(2) != "A"
def c_conf_nous_vous_verbe_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":Y") and m.group(2) != "A"
def c_conf_ait_confiance_été_faim_tort_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:ce que?|tout) ")
def c_conf_veillez2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and morph(dDA, (m.start(2), m.group(2)), ":Y|>ne ", False)
def c_conf_veuillez_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$") and morph(dDA, (m.start(2), m.group(2)), ":Y|>ne ", False)
def c_infi_comment_où_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":M") and not (m.group(1).endswith("ez") and look(s[m.end():], " +vous"))
def s_infi_comment_où_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_qqch_de_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:Q|2p)", ":M")
def s_infi_qqch_de_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_verbe_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ">(?:aimer|aller|désirer|devoir|espérer|pouvoir|préférer|souhaiter|venir) ", ":[GN]") and morphex(dDA, (m.start(2), m.group(2)), ":V", ":M")
def s_infi_verbe_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_devoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">devoir ", False) and morphex(dDA, (m.start(2), m.group(2)), ":V", ":M") and not morph(dDA, prevword1(s, m.start()), ":D", False)
def s_infi_devoir_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_divers_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:Q|2p)", ":M")
def s_infi_divers_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_mieux_valoir_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">valoir ", False) and morphex(dDA, (m.start(2), m.group(2)), ":(?:Q|2p)", ":[GM]")
def s_infi_mieux_valoir_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_à_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V1", ":[NM]") and not m.group(1).istitle() and not look(s[:m.start()], r"(?i)\b(?:les|en) +$")
def s_infi_à_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_infi_avoir_beau_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and morphex(dDA, (m.start(2), m.group(2)), ":V1", ":N")
def s_infi_avoir_beau_1 (s, m):
    return suggVerbInfi(m.group(2))
def c_infi_par_pour_sans_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[Q123][sp]?", ":[YN]")
def s_infi_par_pour_sans_1 (s, m):
    return suggVerbInfi(m.group(1))
def c_ppas_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":V0e", False) and (morphex(dDA, (m.start(2), m.group(2)), ":Y", ":[NAQ]") or m.group(2) in aSHOULDBEVERB) and not re.search("(?i)^(?:soit|été)$", m.group(1)) and not morph(dDA, prevword1(s, m.start()), ":Y|>ce", False, False) and not look(s[:m.start()], "(?i)ce que? +$") and not morph(dDA, prevword1(s, m.start()), ":Y", False, False) and not look_chk1(dDA, s[:m.start()], 0, r"^ *>? *(\w[\w-]+)", ":Y")
def s_ppas_être_1 (s, m):
    return suggVerbPpas(m.group(2))
def c_conj_j_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":1s|>(?:en|y) ")
def c_conj_j_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) == "est" or m.group(1) == "es"
def c_conj_j_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_conj_j_3 (s, m):
    return suggVerb(m.group(1), ":1s")
def c_conj_je_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:1s|G)") and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:1s", False, False))
def c_conj_je_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "est" or m.group(2) == "es"
def c_conj_je_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_conj_je_3 (s, m):
    return suggVerb(m.group(2), ":1s")
def c_conj_j_en_y_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:1s|G|1p)")
def c_conj_j_en_y_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "est" or m.group(2) == "es"
def c_conj_j_en_y_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_conj_j_en_y_3 (s, m):
    return suggVerb(m.group(2), ":1s")
def c_conj_moi_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:1s|G|1p|3p!)")
def c_conj_moi_qui_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "est" or m.group(2) == "es"
def c_conj_moi_qui_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo
def s_conj_moi_qui_3 (s, m):
    return suggVerb(m.group(2), ":1s")
def c_conj_tu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:G|[ISK].*:2s)") and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:2s", False, False))
def s_conj_tu_1 (s, m):
    return suggVerb(m.group(2), ":2s")
def c_conj_toi_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:G|2p|3p!|[ISK].*:2s)")
def s_conj_toi_qui_1 (s, m):
    return suggVerb(m.group(2), ":2s")
def c_conj_il_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|G)") and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:3s", False, False))
def s_conj_il_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_il_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":3p", False)
def c_conj_on_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|G)") and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:3s", False, False))
def s_conj_on_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_quiconque_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:3s|P|G|Q.*:m:[si])")
def s_conj_quiconque_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_ce_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:N|A|3s|P|Q|G|V0e.*:3p)")
def s_conj_ce_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_celui_celle_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|Q|G)")
def s_conj_celui_celle_qui_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_ça_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|Q|G|3p!)") and not morph(dDA, prevword1(s, m.start()), ":[VR]|>de ", False, False)
def s_conj_ça_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_tout_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:3s|P|Q|Y|G|3p!)") and not morph(dDA, prevword1(s, m.start()), ":[VRD]|>de", False, False) and not( morph(dDA, (m.start(1), m.group(1)), ":(?:Y|N.*:m:[si])", False) and not re.search(" (?:qui|>) ", m.group(0)) )
def s_conj_tout_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_tout_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:3s|P|Q|G|3p!)") and not morph(dDA, prevword1(s, m.start()), ":[VRD]|>de", False, False) and not( morph(dDA, (m.start(1), m.group(1)), ":(?:Y|N.*:m:[si])", False) and not re.search(" (?:qui|>) ", m.group(0)) )
def s_conj_tout_qui_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_lequel_laquelle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|Q|G|3p!)") and not morph(dDA, prevword1(s, m.start()), ":[VR]|>de", False, False) and not( morph(dDA, (m.start(2), m.group(2)), ":Y", False) and not re.search(" (?:qui|>) ", m.group(0)) )
def s_conj_lequel_laquelle_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_c_en_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":3s", False)
def s_conj_c_en_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_c_en_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[YP]", False)
def c_conj_elle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|G)") and not morph(dDA, prevword1(s, m.start()), ":R|>(?:et|ou)", False, False) and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:3s", False, False))
def s_conj_elle_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_elle_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":3p", False)
def s_conj_mieux_vaut_1 (s, m):
    return m.group(1)[:-1]+"t"
def c_conj_personne_aucun_rien_nul_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|G)") and morphex(dDA, prevword1(s, m.start()), ":C", ":(?:Y|P|Q|[123][sp]|R)", True) and not( m.group(1).endswith("ien") and look(s[:m.start()], "> +$") and morph(dDA, (m.start(2), m.group(2)), ":Y", False) )
def s_conj_personne_aucun_rien_nul_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_un_une_des_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3s|P|G|Q)") and morphex(dDA, prevword1(s, m.start()), ":C", ":(?:Y|P|Q|[123][sp]|R)", True) and not morph(dDA, (m.start(2), m.group(2)), ":[NA].*:[pi]", False)
def s_conj_un_une_des_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_un_une_des_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3[sp]|P|G)") and morphex(dDA, prevword1(s, m.start()), ":C", ":(?:Y|P|Q|[123][sp]|R)", True)
def s_conj_un_une_des_qui_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_infi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":Y", False) and morph(dDA, (m.start(2), m.group(2)), ":V.[a-z_!?]+(?!.*:(?:3s|P|Q|Y|3p!))")
def s_conj_infi_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_det_sing_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (re.search("(?i)^une? +(?:dizaine|douzaine|quinzaine|vingtaine|trentaine|quarantaine|cinquantaine|soixantaine|centaine|majorité|minorité|millier|partie|poignée|tas|paquet) ", m.group(0)) and morph(dDA, (m.start(3), m.group(3)), ":3p", False)) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:3s|P|Q|Y|3p!|G)") and morphex(dDA, prevword1(s, m.start()), ":C", ":(?:Y|P)", True) and not (look(s[:m.start()], r"(?i)\b(?:et|ou) +$") and morph(dDA, (m.start(3), m.group(3)), ":[123]?p", False)) and not look(s[:m.start()], r"(?i)\bni .* ni ")
def c_conj_det_sing_nom_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not checkAgreement(m.group(2), m.group(3))
def s_conj_det_sing_nom_2 (s, m):
    return suggVerb(m.group(3), ":3s")
def c_conj_det_sing_nom_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and isAmbiguousAndWrong(m.group(2), m.group(3), ":s", ":3s")
def s_conj_det_sing_nom_3 (s, m):
    return suggVerb(m.group(3), ":3s", suggSing)
def c_conj_det_sing_nom_confusion_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not (re.search("(?i)^la +moitié ", m.group(0)) and morph(dDA, (m.start(3), m.group(3)), ":3p", False)) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:3s|P|Q|Y|3p!|G)") and morphex(dDA, prevword1(s, m.start()), ":C", ":(?:Y|P)", True) and not (look(s[:m.start()], r"(?i)\b(?:et|ou) +$") and morph(dDA, (m.start(3), m.group(3)), ":[123]?p", False)) and not look(s[:m.start()], r"(?i)\bni .* ni ")
def c_conj_det_sing_nom_confusion_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not checkAgreement(m.group(2), m.group(3))
def s_conj_det_sing_nom_confusion_2 (s, m):
    return suggVerb(m.group(3), ":3s")
def c_conj_det_sing_nom_confusion_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and isVeryAmbiguousAndWrong(m.group(2), m.group(3), ":s", ":3s", look(s[:m.start()], "^ *$|, *$"))
def s_conj_det_sing_nom_confusion_3 (s, m):
    return suggVerb(m.group(3), ":3s", suggSing)
def c_conj_det_sing_nom_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not ( re.search("(?i)^(?:une? +(?:dizaine|douzaine|quinzaine|vingtaine|trentaine|quarantaine|cinquantaine|soixantaine|centaine|majorité|minorité|millier|partie|poignée|tas|paquet) |la +moitié) ", m.group(0)) and morph(dDA, (m.start(3), m.group(3)), ":3p", False) ) and morphex(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[si]", ":G") and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:3s|P|Q|Y|3p!|G)") and morphex(dDA, prevword1(s, m.start()), ":C", ":(?:Y|P)", True) and not (look(s[:m.start()], r"(?i)\b(?:et|ou) +$") and morph(dDA, (m.start(3), m.group(3)), ":[123]p", False)) and not look(s[:m.start()], r"(?i)\bni .* ni ")
def s_conj_det_sing_nom_qui_1 (s, m):
    return suggVerb(m.group(3), ":3s")
def c_conj_nous_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:1p|3[sp])") and not look(s[m.end():], "^ +(?:je|tu|ils?|elles?|on|[vn]ous)")
def s_conj_nous_pronom_1 (s, m):
    return suggVerb(m.group(1), ":1p")
def c_conj_nous_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":[13]p") and not look(s[m.end():], "^ +(?:je|tu|il|elle|on|[vn]ous)")
def s_conj_nous_qui_1 (s, m):
    return suggVerb(m.group(1), ":1p")
def c_conj_nous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":1p") and not look(s[m.end():], "^ +(?:ils|elles)")
def s_conj_nous_1 (s, m):
    return suggVerb(m.group(1), ":1p")
def c_conj_vous_pronom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:2p|3[sp])") and not look(s[m.end():], "^ +(?:je|ils?|elles?|on|[vn]ous)")
def s_conj_vous_pronom_1 (s, m):
    return suggVerb(m.group(1), ":2p")
def c_conj_vous_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":2p") and not look(s[m.end():], "^ +(?:je|ils?|elles?|on|[vn]ous)")
def s_conj_vous_qui_1 (s, m):
    return suggVerb(m.group(1), ":2p")
def c_conj_ils_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3p|P|Q|G)") and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:3p", False, False))
def s_conj_ils_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_ils_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":3s", False)
def c_conj_ceux_celles_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3p|P|Q|G)")
def s_conj_ceux_celles_qui_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_ceux_là_celles_ci_lesquels_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3p|P|Q|G)") and not morph(dDA, prevword1(s, m.start()), ":[VR]", False, False) and not (morph(dDA, (m.start(2), m.group(2)), ":Y", False) and re.search(r"(?i)lesquel", m.group(1)) and not re.search(" qui |>", m.group(0)))
def s_conj_ceux_là_celles_ci_lesquels_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_elles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3p|P|Q|G)") and not morph(dDA, prevword1(s, m.start()), ":R", False, False) and not (morph(dDA, (m.start(2), m.group(2)), ":[PQ]", False) and morph(dDA, prevword1(s, m.start()), ":V0.*:3p", False, False))
def s_conj_elles_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_elles_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo and morph(dDA, (m.start(2), m.group(2)), ":3s", False)
def c_conf_ont2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"(?i)\b(?:à|avec|sur|chez|par|dans|parmi|contre|ni|de|pour|sous) +$")
def c_conj_beaucoup_d_aucuns_la_plupart_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3p|P|Q|G)") and not morph(dDA, prevword1(s, m.start()), ":[VR]|>de ", False, False)
def s_conj_beaucoup_d_aucuns_la_plupart_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_beaucoup_d_aucuns_la_plupart_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:3p|P|Q|G)") and not morph(dDA, prevword1(s, m.start()), ":[VR]", False, False)
def s_conj_beaucoup_d_aucuns_la_plupart_qui_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_certains_tous_plusieurs_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:G|N|A|3p|P|Q)") and not morph(dDA, prevword1(s, m.start()), ":[VR]", False, False)
def s_conj_certains_tous_plusieurs_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_certains_certaines_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_conj_certains_certaines_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V.*:[123]p", ":[GWM]")
def c_conj_certains_certaines_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1).endswith("n") and morphex(dDA, (m.start(2), m.group(2)), ":V.*:[123]s", ":(?:V0e.*:3s|N.*:[me]:[si])")
def s_conj_certains_certaines_3 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_certains_certaines_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_conj_certains_certaines_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(1).endswith("e") and morphex(dDA, (m.start(2), m.group(2)), ":V.*:[123]s", ":(?:V0e.*:3s|N.*:[fe]:[si])")
def s_conj_certains_certaines_5 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_certains_certaines_6 (s, sx, m, dDA, sCountry, bCondMemo):
    return bCondMemo
def c_conj_det_plur_nom_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:[13]p|P|Y|G|A.*:e:[pi])") and morphex(dDA, prevword1(s, m.start()), ":C", ":[YP]", True) and not( morph(dDA, (m.start(3), m.group(3)), ":3s", False) and look(s[:m.start()], r"(?i)\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") )
def c_conj_det_plur_nom_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not checkAgreement(m.group(2), m.group(3))
def s_conj_det_plur_nom_2 (s, m):
    return suggVerb(m.group(3), ":3p")
def c_conj_det_plur_nom_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and isAmbiguousAndWrong(m.group(2), m.group(3), ":p", ":3p")
def s_conj_det_plur_nom_3 (s, m):
    return suggVerb(m.group(3), ":3p", suggPlur)
def c_conj_det_plur_nom_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:[13]p|P|Y|G|A.*:e:[pi])") and morphex(dDA, prevword1(s, m.start()), ":C", ":[YP]", True) and not( morph(dDA, (m.start(3), m.group(3)), ":3s", False) and look(s[:m.start()], r"(?i)\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") )
def s_conj_det_plur_nom_qui_1 (s, m):
    return suggVerb(m.group(3), ":3p")
def c_conj_det_plur_nom_confusion_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:[13]p|P|Y|G|A.*:e:[pi])") and morphex(dDA, prevword1(s, m.start()), ":C", ":[YP]", True) and not( morph(dDA, (m.start(3), m.group(3)), ":3s", False) and look(s[:m.start()], r"(?i)\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") )
def c_conj_det_plur_nom_confusion_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not checkAgreement(m.group(2), m.group(3))
def s_conj_det_plur_nom_confusion_2 (s, m):
    return suggVerb(m.group(3), ":3p")
def c_conj_det_plur_nom_confusion_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and (m.group(1) == "les" or m.group(1) == "Les") and isVeryAmbiguousAndWrong(m.group(2), m.group(3), ":p", ":3p", look(s[:m.start()], "^ *$|, *$"))
def s_conj_det_plur_nom_confusion_3 (s, m):
    return suggVerb(m.group(3), ":3p", suggPlur)
def c_conj_det_plur_nom_confusion_4 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and (m.group(1) == "certains" or m.group(1) == "Certains") and isVeryAmbiguousAndWrong(m.group(2), m.group(3), ":m:p", ":3p", look(s[:m.start()], "^ *$|, *$"))
def s_conj_det_plur_nom_confusion_4 (s, m):
    return suggVerb(m.group(3), ":3p", suggMasPlur)
def c_conj_det_plur_nom_confusion_5 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and (m.group(1) == "certaines" or m.group(1) == "Certaines") and isVeryAmbiguousAndWrong(m.group(2), m.group(3), ":f:p", ":3p", look(s[:m.start()], "^ *$|, *$"))
def s_conj_det_plur_nom_confusion_5 (s, m):
    return suggVerb(m.group(3), ":3p", suggFemPlur)
def c_conj_det_plur_nom_qui_confusion_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(3), m.group(3)), ":V", ":(?:[13]p|P|Q|Y|G|A.*:e:[pi])") and morphex(dDA, prevword1(s, m.start()), ":C", ":[YP]", True) and not( morph(dDA, (m.start(3), m.group(3)), ":3s", False) and look(s[:m.start()], r"(?i)\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") )
def s_conj_det_plur_nom_qui_confusion_1 (s, m):
    return suggVerb(m.group(3), ":3p")
def c_conj_des_nom1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:[13]p|P|G|Q|A.*:[pi])") and morph(dDA, nextword1(s, m.end()), ":(?:R|D.*:p)|>au ", False, True)
def c_conj_des_nom1_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(2), m.group(2)), ":[NA]", False)
def s_conj_des_nom1_2 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_des_nom1_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and not checkAgreement(m.group(1), m.group(2))
def s_conj_des_nom1_3 (s, m):
    return suggVerb(m.group(2), ":3p", suggPlur)
def c_conj_des_nom_qui_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":[NAQ].*:[pi]", False) and morphex(dDA, (m.start(2), m.group(2)), ":V", ":(?:[13]p|P|G)")
def s_conj_des_nom_qui_1 (s, m):
    return suggVerb(m.group(2), ":3p")
def c_conj_quel_quelle_que_3sg1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V0e", ":3s")
def s_conj_quel_quelle_que_3sg1_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_quel_quelle_que_3sg2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V0e.*:3s", ":3p")
def s_conj_quel_quelle_que_3sg2_1 (s, m):
    return m.group(1)[:-1]
def c_conj_quels_quelles_que_3pl1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V0e", ":3p")
def s_conj_quels_quelles_que_3pl1_1 (s, m):
    return suggVerb(m.group(1), ":3p")
def c_conj_quels_quelles_que_3pl2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":V0e.*:3p", ":3s")
def c_conj_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return not look(s[:m.start()], r"\b(?:et |ou |[dD][eu] |ni |[dD]e l’) *$") and morph(dDA, (m.start(1), m.group(1)), ":M", False) and morphex(dDA, (m.start(2), m.group(2)), ":[123][sp]", ":(?:G|3s|3p!|P|M|[AQ].*:[si])") and not morph(dDA, prevword1(s, m.start()), ":[VRD]", False, False) and not look(s[:m.start()], r"([A-ZÉÈ][\w-]+), +([A-ZÉÈ][\w-]+), +$") and not (morph(dDA, (m.start(2), m.group(2)), ":3p", False) and prevword1(s, m.start()))
def s_conj_nom_propre_1 (s, m):
    return suggVerb(m.group(2), ":3s")
def c_conj_nom_propre_et_nom_propre_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":M", False) and morph(dDA, (m.start(2), m.group(2)), ":M", False) and morphex(dDA, (m.start(3), m.group(3)), ":[123][sp]", ":(?:G|3p|P|Q.*:[pi])") and not morph(dDA, prevword1(s, m.start()), ":R", False, False)
def s_conj_nom_propre_et_nom_propre_1 (s, m):
    return suggVerb(m.group(3), ":3p")
def c_conj_que_où_comment_verbe_sujet_sing_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":(?:[12]s|3p)", ":(?:3s|G|W|3p!)") and not look(s[m.end():], "^ +(?:et|ou) (?:l(?:es? |a |’|eurs? )|[mts](?:a|on|es) |ce(?:tte|ts|) |[nv]o(?:s|tre) |d(?:u|es) )")
def s_conj_que_où_comment_verbe_sujet_sing_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_que_où_comment_verbe_sujet_pluriel_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[123]s", ":(?:3p|G|W)")
def s_conj_que_où_comment_verbe_sujet_pluriel_1 (s, m):
    return suggVerb(m.group(1), ":3p")
def c_conj_que_où_comment_verbe_sujet_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[12][sp]", ":(?:G|W|3[sp]|Y|P|Q|N|M)")
def s_conj_que_où_comment_verbe_sujet_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_conj_puisse_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return look(s[:m.start()], "^ *$|, *$")
def c_conj_puisse_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":D.*:p", False)
def c_conj_puisse_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not bCondMemo and m.group(1).endswith("s") and m.group(2) != "tu" and not look(s[:m.start()], r"(?i)\btu ")
def c_inte_union_xxxe_je_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:1[sŝś]", ":[GNW]") and not look(s[:m.start()], r"(?i)\bje +$") and morphex(dDA, nextword1(s, m.end()), ":", ":(?:Oo|X|1s)", True)
def s_inte_union_xxxe_je_1 (s, m):
    return m.group(1)[:-1]+"é-je"
def c_inte_union_xxx_je_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:1s", ":[GNW]") and not look(s[:m.start()], r"(?i)\b(?:je|tu) +$") and morphex(dDA, nextword1(s, m.end()), ":", ":(?:Oo|X|1s)", True)
def c_inte_union_tu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:2s", ":[GNW]") and not look(s[:m.start()], r"(?i)\b(?:je|tu) +$") and morphex(dDA, nextword1(s, m.end()), ":", ":2s", True)
def c_inte_union_il_on_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:3s", ":[GNW]") and not look(s[:m.start()], r"(?i)\b(?:ce|il|elle|on) +$") and morphex(dDA, nextword1(s, m.end()), ":", ":3s|>y ", True)
def s_inte_union_il_on_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_inte_union_elle_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:3s", ":[GNW]") and not look(s[:m.start()], r"(?i)\b(?:ce|il|elle|on) +$") and morphex(dDA, nextword1(s, m.end()), ":", ":3s", True)
def c_inte_union_nous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:1p", ":[GNW]") and not morph(dDA, prevword1(s, m.start()), ":Os", False, False) and morphex(dDA, nextword1(s, m.end()), ":", ":(?:Y|1p)", True)
def c_inte_union_vous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:2p", ":[GNW]|>vouloir .*:E:2p") and not morph(dDA, prevword1(s, m.start()), ":Os", False, False) and morphex(dDA, nextword1(s, m.end()), ":", ":(?:Y|2p)", True)
def c_inte_union_ils_elles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V.*:3p", ":[GNW]") and not look(s[:m.start()], r"(?i)\b(?:ce|ils|elles) +$") and morphex(dDA, nextword1(s, m.end()), ":", ":3p", True)
def s_inte_union_ils_elles_1 (s, m):
    return m.group(0).replace(" ", "-")
def c_inte_je_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":1[sśŝ]")
def s_inte_je_1 (s, m):
    return suggVerb(m.group(1), ":1ś")
def c_inte_je_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":V", False)
def s_inte_je_2 (s, m):
    return suggSimil(m.group(1), ":1[sśŝ]", False)
def c_inte_tu_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":[ISK].*:2s")
def s_inte_tu_1 (s, m):
    return suggVerb(m.group(1), ":2s")
def c_inte_tu_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":V", False)
def s_inte_tu_2 (s, m):
    return suggSimil(m.group(1), ":2s", False)
def c_inte_il_elle_on_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":3s")
def s_inte_il_elle_on_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_inte_il_elle_on_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "t" and (not m.group(1).endswith("oilà") or m.group(2) != "il") and morphex(dDA, (m.start(1), m.group(1)), ":", ":V")
def s_inte_il_elle_on_2 (s, m):
    return suggSimil(m.group(1), ":3s", False)
def c_inte_il_elle_on_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return not m.group(2).endswith(("n", "N")) and morphex(dDA, (m.start(1), m.group(1)), ":3p", ":3s")
def c_inte_ce_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:3s|V0e.*:3p)")
def s_inte_ce_1 (s, m):
    return suggVerb(m.group(1), ":3s")
def c_inte_ce_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":V")
def s_inte_ce_2 (s, m):
    return suggSimil(m.group(1), ":3s", False)
def c_inte_ce_3 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(2) == "se"
def c_inte_nous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":(?:1p|E:2[sp])")
def s_inte_nous_1 (s, m):
    return suggVerb(m.group(1), ":1p")
def c_inte_nous_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":", ":V|>chez ")
def s_inte_nous_2 (s, m):
    return suggSimil(m.group(1), ":1p", False)
def c_inte_vous_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":2p")
def s_inte_vous_1 (s, m):
    return suggVerb(m.group(1), ":2p")
def c_inte_vous_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return not morph(dDA, (m.start(1), m.group(1)), ":V|>chez ", False)
def s_inte_vous_2 (s, m):
    return suggSimil(m.group(1), ":2p", False)
def c_inte_ils_elles_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":V", ":3p") and _oSpellChecker.isValid(m.group(1))
def s_inte_ils_elles_1 (s, m):
    return suggVerb(m.group(1), ":3p")
def c_inte_ils_elles_2 (s, sx, m, dDA, sCountry, bCondMemo):
    return m.group(1) != "t" and not morph(dDA, (m.start(1), m.group(1)), ":V", False) and _oSpellChecker.isValid(m.group(1))
def s_inte_ils_elles_2 (s, m):
    return suggSimil(m.group(1), ":3p", False)
def c_conf_avoir_sujet_participe_passé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and morph(dDA, (m.start(2), m.group(2)), ":V.......e_.*:Q", False)
def c_conf_sujet_avoir_participe_passé_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">avoir ", False) and morph(dDA, (m.start(2), m.group(2)), ":V.......e_.*:Q", False)
def c_vmode_j_aimerais_vinfi_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":[YX]|>(?:y|ne|que?) ", ":R") and look(s[:m.start()], "^ *$|, *$")
def c_vmode_j_aurais_aimé_que_avoir_être_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(2), m.group(2)), ":Y|>(?:ne|que?) ", False)
def c_vmode_si_sujet1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Os|M)", False) and morphex(dDA, (m.start(2), m.group(2)), ":[SK]", ":(?:G|V0|I)") and look(s[:m.start()], "^ *$|, *$")
def c_vmode_si_sujet2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":[SK]", ":(?:G|V0|I)") and look(s[:m.start()], "^ *$|, *$")
def c_vmode_dès_que_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Os|M)", False) and morphex(dDA, (m.start(2), m.group(2)), ":S", ":[IG]")
def s_vmode_dès_que_1 (s, m):
    return suggVerbMode(m.group(2), ":I", m.group(1))
def c_vmode_qqch_que_subjonctif1_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ">(?:afin|avant|pour|quoi|permettre|falloir|vouloir|ordonner|exiger|désirer|douter|préférer|suffire) ", False) and morph(dDA, (m.start(2), m.group(2)), ":(?:Os|M)", False) and morphex(dDA, (m.start(3), m.group(3)), ":I", ":[GYS]") and not (morph(dDA, (m.start(1), m.group(1)), ">douter ", False) and morph(dDA, (m.start(3), m.group(3)), ":(?:If|K)", False))
def s_vmode_qqch_que_subjonctif1_1 (s, m):
    return suggVerbMode(m.group(3), ":S", m.group(2))
def c_vmode_bien_que_subjonctif_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Os|M)", False) and morphex(dDA, (m.start(2), m.group(2)), ":V.*:I", ":(?:[GSK]|If)|>(?:hériter|recevoir|donner|offrir) ") and look(s[:m.start()], "^ *$|, *$") and not ( morph(dDA, (m.start(2), m.group(2)), ":V0a", False) and morph(dDA, nextword1(s, m.end()), ">(?:hériter|recevoir|donner|offrir) ", False) ) and not look(sx[:m.start()], r"(?i)\bsi ")
def s_vmode_bien_que_subjonctif_1 (s, m):
    return suggVerbMode(m.group(2), ":S", m.group(1))
def c_vmode_qqch_que_subjonctif2_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Os|M)", False) and morphex(dDA, (m.start(2), m.group(2)), ":", ":[GYS]")
def s_vmode_qqch_que_subjonctif2_1 (s, m):
    return suggVerbMode(m.group(2), ":S", m.group(1))
def c_vmode_sujet_indicatif_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(2), m.group(2)), ":S", ":[GIK]") and not re.search("^e(?:usse|û[mt]es|ût)", m.group(2))
def s_vmode_sujet_indicatif_1 (s, m):
    return suggVerbMode(m.group(2), ":I", m.group(1))
def c_vmode_j_indicatif_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morphex(dDA, (m.start(1), m.group(1)), ":S", ":[GIK]") and m.group(1) != "eusse"
def s_vmode_j_indicatif_1 (s, m):
    return suggVerbMode(m.group(1), ":I", "je")
def c_vmode_après_que_indicatif_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Os|M)", False) and (morphex(dDA, (m.start(2), m.group(2)), ":V.*:S", ":[GI]") or morph(dDA, (m.start(2), m.group(2)), ":V0e.*:S", False))
def s_vmode_après_que_indicatif_1 (s, m):
    return suggVerbMode(m.group(2), ":I", m.group(1))
def c_vmode_quand_lorsque_indicatif_1 (s, sx, m, dDA, sCountry, bCondMemo):
    return morph(dDA, (m.start(1), m.group(1)), ":(?:Os|M)", False) and (morphex(dDA, (m.start(2), m.group(2)), ":V.*:S", ":[GI]") or morph(dDA, (m.start(2), m.group(2)), ":V0e.*:S", False))
def s_vmode_quand_lorsque_indicatif_1 (s, m):
    return suggVerbMode(m.group(2), ":I", m.group(1))

