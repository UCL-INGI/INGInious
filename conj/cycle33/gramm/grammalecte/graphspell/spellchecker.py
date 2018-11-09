# Spellchecker
# Wrapper for the IBDAWG class.
# Useful to check several dictionaries at once.

# To avoid iterating over a pile of dictionaries, it is assumed that 3 are enough:
# - the main dictionary, bundled with the package
# - the extended dictionary, added by an organization
# - the personal dictionary, created by the user for its own convenience


import traceback

from . import ibdawg
from . import tokenizer


dDefaultDictionaries = {
    "fr": "fr.bdic",
    "en": "en.bdic"
}


class SpellChecker ():

    def __init__ (self, sLangCode, sfMainDic="", sfExtendedDic="", sfPersonalDic=""):
        "returns True if the main dictionary is loaded"
        self.sLangCode = sLangCode
        if not sfMainDic:
            sfMainDic = dDefaultDictionaries.get(sLangCode, "")
        self.oMainDic = self._loadDictionary(sfMainDic, True)
        self.oExtendedDic = self._loadDictionary(sfExtendedDic)
        self.oPersonalDic = self._loadDictionary(sfPersonalDic)
        self.oTokenizer = None

    def _loadDictionary (self, sfDictionary, bNecessary=False):
        "returns an IBDAWG object"
        if not sfDictionary:
            return None
        try:
            return ibdawg.IBDAWG(sfDictionary)
        except Exception as e:
            if bNecessary:
                raise Exception(str(e), "Error: <" + sfDictionary + "> not loaded.")
            print("Error: <" + sfDictionary + "> not loaded.")
            traceback.print_exc()
            return None

    def loadTokenizer (self):
        self.oTokenizer = tokenizer.Tokenizer(self.sLangCode)

    def getTokenizer (self):
        if not self.oTokenizer:
            self.loadTokenizer()
        return self.oTokenizer

    def setMainDictionary (self, sfDictionary):
        "returns True if the dictionary is loaded"
        self.oMainDic = self._loadDictionary(sfDictionary)
        return bool(self.oMainDic)
            
    def setExtendedDictionary (self, sfDictionary):
        "returns True if the dictionary is loaded"
        self.oExtendedDic = self._loadDictionary(sfDictionary)
        return bool(self.oExtendedDic)

    def setPersonalDictionary (self, sfDictionary):
        "returns True if the dictionary is loaded"
        self.oPersonalDic = self._loadDictionary(sfDictionary)
        return bool(self.oPersonalDic)

    # parse text functions

    def parseParagraph (self, sText, bSpellSugg=False):
        if not self.oTokenizer:
            self.loadTokenizer()
        aSpellErrs = []
        for dToken in self.oTokenizer.genTokens(sText):
            if dToken['sType'] == "WORD" and not self.isValidToken(dToken['sValue']):
                if bSpellSugg:
                    dToken['aSuggestions'] = []
                    for lSugg in self.suggest(dToken['sValue']):
                        dToken['aSuggestions'].extend(lSugg)
                aSpellErrs.append(dToken)
        return aSpellErrs

    def countWordsOccurrences (self, sText, bByLemma=False, bOnlyUnknownWords=False, dWord={}):
        if not self.oTokenizer:
            self.loadTokenizer()
        for dToken in self.oTokenizer.genTokens(sText):
            if dToken['sType'] == "WORD":
                if bOnlyUnknownWords:
                    if not self.isValidToken(dToken['sValue']):
                        dWord[dToken['sValue']] = dWord.get(dToken['sValue'], 0) + 1
                else:
                    if not bByLemma:
                        dWord[dToken['sValue']] = dWord.get(dToken['sValue'], 0) + 1
                    else:
                        for sLemma in self.getLemma(dToken['sValue']):
                            dWord[sLemma] = dWord.get(sLemma, 0) + 1
        return dWord

    # IBDAWG functions

    def isValidToken (self, sToken):
        "checks if sToken is valid (if there is hyphens in sToken, sToken is split, each part is checked)"
        if self.oMainDic.isValidToken(sToken):
            return True
        if self.oExtendedDic and self.oExtendedDic.isValidToken(sToken):
            return True
        if self.oPersonalDic and self.oPersonalDic.isValidToken(sToken):
            return True
        return False

    def isValid (self, sWord):
        "checks if sWord is valid (different casing tested if the first letter is a capital)"
        if self.oMainDic.isValid(sWord):
            return True
        if self.oExtendedDic and self.oExtendedDic.isValid(sWord):
            return True
        if self.oPersonalDic and self.oPersonalDic.isValid(sWord):
            return True
        return False

    def lookup (self, sWord):
        "checks if sWord is in dictionary as is (strict verification)"
        if self.oMainDic.lookup(sWord):
            return True
        if self.oExtendedDic and self.oExtendedDic.lookup(sWord):
            return True
        if self.oPersonalDic and self.oPersonalDic.lookup(sWord):
            return True
        return False

    def getMorph (self, sWord):
        "retrieves morphologies list, different casing allowed"
        lResult = self.oMainDic.getMorph(sWord)
        if self.oExtendedDic:
            lResult.extend(self.oExtendedDic.getMorph(sWord))
        if self.oPersonalDic:
            lResult.extend(self.oPersonalDic.getMorph(sWord))
        return lResult

    def getLemma (self, sWord):
        return set([ s[1:s.find(" ")]  for s in self.getMorph(sWord) ])

    def suggest (self, sWord, nSuggLimit=10):
        "generator: returns 1, 2 or 3 lists of suggestions"
        yield self.oMainDic.suggest(sWord, nSuggLimit)
        if self.oExtendedDic:
            yield self.oExtendedDic.suggest(sWord, nSuggLimit)
        if self.oPersonalDic:
            yield self.oPersonalDic.suggest(sWord, nSuggLimit)

    def select (self, sPattern=""):
        "generator: returns all entries which morphology fits <sPattern>"
        yield from self.oMainDic.select(sPattern)
        if self.oExtendedDic:
            yield from self.oExtendedDic.select(sPattern)
        if self.oPersonalDic:
            yield from self.oPersonalDic.select(sPattern)

    def drawPath (self, sWord):
        self.oMainDic.drawPath(sWord)
        if self.oExtendedDic:
            print("-----")
            self.oExtendedDic.drawPath(sWord)
        if self.oPersonalDic:
            print("-----")
            self.oPersonalDic.drawPath(sWord)
