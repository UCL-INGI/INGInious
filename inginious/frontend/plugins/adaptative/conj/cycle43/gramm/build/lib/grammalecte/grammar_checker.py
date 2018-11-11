# Grammalecte
# Main class: wrapper

import importlib
import json

from . import text


class GrammarChecker:

    def __init__ (self, sLangCode, sContext="Python"):
        self.sLangCode = sLangCode
        # Grammar checker engine
        self.gce = importlib.import_module("."+sLangCode, "grammalecte")
        self.gce.load(sContext)
        # Spell checker
        self.oSpellChecker = self.gce.getSpellChecker()
        # Lexicographer
        self.oLexicographer = None
        # Text formatter
        self.oTextFormatter = None

    def getGCEngine (self):
        return self.gce

    def getSpellChecker (self):
        return self.oSpellChecker

    def getTextFormatter (self):
        if self.oTextFormatter == None:
            self.tf = importlib.import_module("."+self.sLangCode+".textformatter", "grammalecte")
        self.oTextFormatter = self.tf.TextFormatter()
        return self.oTextFormatter

    def getLexicographer (self):
        if self.oLexicographer == None:
            self.lxg = importlib.import_module("."+self.sLangCode+".lexicographe", "grammalecte")
        self.oLexicographer = self.lxg.Lexicographe(self.oSpellChecker)
        return self.oLexicographer

    def displayGCOptions (self):
        self.gce.displayOptions()

    def getParagraphErrors (self, sText, dOptions=None, bContext=False, bSpellSugg=False, bDebug=False):
        "returns a tuple: (grammar errors, spelling errors)"
        aGrammErrs = self.gce.parse(sText, "FR", bDebug=bDebug, dOptions=dOptions, bContext=bContext)
        aSpellErrs = self.oSpellChecker.parseParagraph(sText, bSpellSugg)
        return aGrammErrs, aSpellErrs

    def generateText (self, sText, bEmptyIfNoErrors=False, bSpellSugg=False, nWidth=100, bDebug=False):
        pass

    def generateTextAsJSON (self, sText, bContext=False, bEmptyIfNoErrors=False, bSpellSugg=False, bReturnText=False, bDebug=False):
        pass

    def generateParagraph (self, sText, dOptions=None, bEmptyIfNoErrors=False, bSpellSugg=False, nWidth=100, bDebug=False):
        aGrammErrs, aSpellErrs = self.getParagraphErrors(sText, dOptions, False, bSpellSugg, bDebug)
        if bEmptyIfNoErrors and not aGrammErrs and not aSpellErrs:
            return ""
        return text.generateParagraph(sText, aGrammErrs, aSpellErrs, nWidth)

    def generateParagraphAsJSON (self, iIndex, sText, dOptions=None, bContext=False, bEmptyIfNoErrors=False, bSpellSugg=False, bReturnText=False, lLineSet=None, bDebug=False):
        aGrammErrs, aSpellErrs = self.getParagraphErrors(sText, dOptions, bContext, bSpellSugg, bDebug)
        aGrammErrs = list(aGrammErrs)
        if bEmptyIfNoErrors and not aGrammErrs and not aSpellErrs:
            return ""
        if lLineSet:
            aGrammErrs, aSpellErrs = text.convertToXY(aGrammErrs, aSpellErrs, lLineSet)
            return json.dumps({ "lGrammarErrors": aGrammErrs, "lSpellingErrors": aSpellErrs }, ensure_ascii=False)
        if bReturnText:
            return json.dumps({ "iParagraph": iIndex, "sText": sText, "lGrammarErrors": aGrammErrs, "lSpellingErrors": aSpellErrs }, ensure_ascii=False)
        return json.dumps({ "iParagraph": iIndex, "lGrammarErrors": aGrammErrs, "lSpellingErrors": aSpellErrs }, ensure_ascii=False)
