#!python3

import os
import traceback
import pkgutil
import re
from functools import wraps
import time
import json
import binascii

#import logging
#logging.basicConfig(filename="suggestions.log", level=logging.DEBUG)

from . import str_transform as st
from . import char_player as cp
from .echo import echo


def timethis (func):
    "decorator for the execution time"
    @wraps(func)
    def wrapper (*args, **kwargs):
        fStart = time.time()
        result = func(*args, **kwargs)
        fEnd = time.time()
        print(func.__name__, fEnd - fStart)
        return result
    return wrapper


class SuggResult:
    """Structure for storing, classifying and filtering suggestions"""

    def __init__ (self, sWord, nDistLimit=-1):
        self.sWord = sWord
        self.sSimplifiedWord = cp.simplifyWord(sWord)
        self.nDistLimit = nDistLimit  if nDistLimit >= 0  else  (len(sWord) // 3) + 1
        self.nMinDist = 1000
        self.aSugg = set()
        self.dSugg = { 0: [],  1: [],  2: [] }

    def addSugg (self, sSugg, nDeep=0):
        "add a suggestion"
        #logging.info((nDeep * "  ") + "__" + sSugg + "__")
        if sSugg not in self.aSugg:
            nDist = st.distanceDamerauLevenshtein(self.sSimplifiedWord, cp.simplifyWord(sSugg))
            if nDist <= self.nDistLimit:
                if nDist not in self.dSugg:
                    self.dSugg[nDist] = []
                self.dSugg[nDist].append(sSugg)
                self.aSugg.add(sSugg)
                if nDist < self.nMinDist:
                    self.nMinDist = nDist
                self.nDistLimit = min(self.nDistLimit, self.nMinDist+2)

    def getSuggestions (self, nSuggLimit=10, nDistLimit=-1):
        "return a list of suggestions"
        lRes = []
        if self.dSugg[0]:
            # we sort the better results with the original word
            self.dSugg[0].sort(key=lambda sSugg: st.distanceDamerauLevenshtein(self.sWord, sSugg))
        for lSugg in self.dSugg.values():
            lRes.extend(lSugg)
            if len(lRes) > nSuggLimit:
                break
        lRes = list(cp.filterSugg(lRes))
        if self.sWord.istitle():
            lRes = list(map(lambda sSugg: sSugg.title(), lRes))
        elif self.sWord.isupper():
            lRes = list(map(lambda sSugg: sSugg.upper(), lRes))
        return lRes[:nSuggLimit]

    def reset (self):
        self.aSugg.clear()
        self.dSugg.clear()


class IBDAWG:
    """INDEXABLE BINARY DIRECT ACYCLIC WORD GRAPH"""

    def __init__ (self, sfDict):
        self.by = pkgutil.get_data(__package__, "_dictionaries/" + sfDict)
        if not self.by:
            raise OSError("# Error. File not found or not loadable: "+sfDict)

        if sfDict.endswith(".bdic"):
            self._initBinary()
        elif sfDict.endswith(".json"):
            self._initJSON()
        else:
            raise OSError("# Error. Unknown file type: "+sfDict)

        self.sFileName = sfDict

        self._arcMask = (2 ** ((self.nBytesArc * 8) - 3)) - 1
        self._finalNodeMask = 1 << ((self.nBytesArc * 8) - 1)
        self._lastArcMask = 1 << ((self.nBytesArc * 8) - 2)
        self._addrBitMask = 1 << ((self.nBytesArc * 8) - 3)  # version 2

        # function to decode the affix/suffix code
        if self.cStemming == "S":
            self.funcStemming = st.changeWordWithSuffixCode
        elif self.cStemming == "A":
            self.funcStemming = st.changeWordWithAffixCode
        else:
            self.funcStemming = st.noStemming

        # Configuring DAWG functions according to nCompressionMethod
        if self.nCompressionMethod == 1:
            self.morph = self._morph1
            self.stem = self._stem1
            self._lookupArcNode = self._lookupArcNode1
            self._getArcs = self._getArcs1
            self._writeNodes = self._writeNodes1
        elif self.nCompressionMethod == 2:
            self.morph = self._morph2
            self.stem = self._stem2
            self._lookupArcNode = self._lookupArcNode2
            self._getArcs = self._getArcs2
            self._writeNodes = self._writeNodes2
        elif self.nCompressionMethod == 3:
            self.morph = self._morph3
            self.stem = self._stem3
            self._lookupArcNode = self._lookupArcNode3
            self._getArcs = self._getArcs3
            self._writeNodes = self._writeNodes3
        else:
            raise ValueError("  # Error: unknown code: {}".format(self.nCompressionMethod))

        self.bOptNumSigle = False
        self.bOptNumAtLast = False

    def _initBinary (self):
        "initialize with binary structure file"
        if self.by[0:7] != b"/pyfsa/":
            raise TypeError("# Error. Not a pyfsa binary dictionary. Header: {}".format(self.by[0:9]))
        if not(self.by[7:8] == b"1" or self.by[7:8] == b"2" or self.by[7:8] == b"3"):
            raise ValueError("# Error. Unknown dictionary version: {}".format(self.by[7:8]))
        try:
            header, info, values, bdic = self.by.split(b"\0\0\0\0", 3)
        except Exception:
            raise Exception
        
        self.nCompressionMethod = int(self.by[7:8].decode("utf-8"))
        self.sHeader = header.decode("utf-8")
        self.lArcVal = values.decode("utf-8").split("\t")
        self.nArcVal = len(self.lArcVal)
        self.byDic = bdic

        l = info.decode("utf-8").split("//")
        self.sLangCode = l.pop(0)
        self.sLangName = l.pop(0)
        self.sDicName = l.pop(0)
        self.sDate = l.pop(0)
        self.nChar = int(l.pop(0))
        self.nBytesArc = int(l.pop(0))
        self.nBytesNodeAddress = int(l.pop(0))
        self.nEntry = int(l.pop(0))
        self.nNode = int(l.pop(0))
        self.nArc = int(l.pop(0))
        self.nAff = int(l.pop(0))
        self.cStemming = l.pop(0)
        self.nTag = self.nArcVal - self.nChar - self.nAff
        # <dChar> to get the value of an arc, <dCharVal> to get the char of an arc with its value
        self.dChar = {}
        for i in range(1, self.nChar+1):
            self.dChar[self.lArcVal[i]] = i
        self.dCharVal = { v: k  for k, v in self.dChar.items() }
        self.nBytesOffset = 1 # version 3

    def _initJSON (self):
        "initialize with a JSON text file"
        self.__dict__.update(json.loads(self.by.decode("utf-8")))
        #self.__dict__.update(json.loads(self.by))                  # In Python 3.6, can read directly binary strings
        self.byDic = binascii.unhexlify(self.sByDic)

    def getInfo (self):
        return  "  Language: {0.sLangName}   Lang code: {0.sLangCode}   Dictionary name: {0.sDicName}" \
                "  Compression method: {0.nCompressionMethod:>2}   Date: {0.sDate}   Stemming: {0.cStemming}FX\n" \
                "  Arcs values:  {0.nArcVal:>10,} = {0.nChar:>5,} characters,  {0.nAff:>6,} affixes,  {0.nTag:>6,} tags\n" \
                "  Dictionary: {0.nEntry:>12,} entries,    {0.nNode:>11,} nodes,   {0.nArc:>11,} arcs\n" \
                "  Address size: {0.nBytesNodeAddress:>1} bytes,  Arc size: {0.nBytesArc:>1} bytes\n".format(self)

    def writeAsJSObject (self, spfDest, bInJSModule=False, bBinaryDictAsHexString=False):
        "write IBDAWG as a JavaScript object in a JavaScript module"
        with open(spfDest, "w", encoding="utf-8", newline="\n") as hDst:
            if bInJSModule:
                hDst.write('// JavaScript\n// Generated data (do not edit)\n\n"use strict";\n\nconst dictionary = ')
            hDst.write(json.dumps({
                            "sHeader": "/pyfsa/",
                            "sLangCode": self.sLangCode,
                            "sLangName": self.sLangName,
                            "sDicName": self.sDicName,
                            "sFileName": self.sFileName,
                            "sDate": self.sDate,
                            "nEntry": self.nEntry,
                            "nChar": self.nChar,
                            "nAff": self.nAff,
                            "nTag": self.nTag,
                            "cStemming": self.cStemming,
                            "dChar": self.dChar,
                            "nNode": self.nNode,
                            "nArc": self.nArc,
                            "nArcVal": self.nArcVal,
                            "lArcVal": self.lArcVal,
                            "nCompressionMethod": self.nCompressionMethod,
                            "nBytesArc": self.nBytesArc,
                            "nBytesNodeAddress": self.nBytesNodeAddress,
                            "nBytesOffset": self.nBytesOffset,
                            # JavaScript is a pile of shit, so Mozilla’s JS parser don’t like file bigger than 4 Mb!
                            # So, if necessary, we use an hexadecimal string, that we will convert later in Firefox’s extension.
                            # https://github.com/mozilla/addons-linter/issues/1361
                            "sByDic": self.byDic.hex()  if bBinaryDictAsHexString  else [ e  for e in self.byDic ]
                        }, ensure_ascii=False))
            if bInJSModule:
                hDst.write(";\n\nexports.dictionary = dictionary;\n")

    def isValidToken (self, sToken):
        "checks if <sToken> is valid (if there is hyphens in <sToken>, <sToken> is split, each part is checked)"
        sToken = cp.spellingNormalization(sToken)
        if self.isValid(sToken):
            return True
        if "-" in sToken:
            if sToken.count("-") > 4:
                return True
            return all(self.isValid(sWord)  for sWord in sToken.split("-"))
        return False

    def isValid (self, sWord):
        "checks if <sWord> is valid (different casing tested if the first letter is a capital)"
        if not sWord:
            return None
        if "’" in sWord: # ugly hack
            sWord = sWord.replace("’", "'")
        if self.lookup(sWord):
            return True
        if sWord[0:1].isupper():
            if len(sWord) > 1:
                if sWord.istitle():
                    return self.lookup(sWord.lower())
                if sWord.isupper():
                    if self.bOptNumSigle:
                        return True
                    return self.lookup(sWord.lower()) or self.lookup(sWord.capitalize())
                return self.lookup(sWord[:1].lower() + sWord[1:])
            else:
                return self.lookup(sWord.lower())
        return False

    def lookup (self, sWord):
        "returns True if <sWord> in dictionary (strict verification)"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return False
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return False
        return bool(int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask)

    def getMorph (self, sWord):
        "retrieves morphologies list, different casing allowed"
        sWord = cp.spellingNormalization(sWord)
        l = self.morph(sWord)
        if sWord[0:1].isupper():
            l.extend(self.morph(sWord.lower()))
            if sWord.isupper() and len(sWord) > 1:
                l.extend(self.morph(sWord.capitalize()))
        return l

    #@timethis
    def suggest (self, sWord, nSuggLimit=10):
        "returns a set of suggestions for <sWord>"
        sWord = cp.spellingNormalization(sWord)
        sPfx, sWord, sSfx = cp.cut(sWord)
        nMaxSwitch = max(len(sWord) // 3, 1)
        nMaxDel = len(sWord) // 5
        nMaxHardRepl = max((len(sWord) - 5) // 4, 1)
        oSuggResult = SuggResult(sWord)
        self._suggest(oSuggResult, sWord, nMaxSwitch=nMaxSwitch, nMaxDel=nMaxDel, nMaxHardRepl=nMaxHardRepl)
        if sWord.istitle():
            self._suggest(oSuggResult, sWord.lower(), nMaxSwitch=nMaxSwitch, nMaxDel=nMaxDel, nMaxHardRepl=nMaxHardRepl)
        elif sWord.islower():
            self._suggest(oSuggResult, sWord.title(), nMaxSwitch=nMaxSwitch, nMaxDel=nMaxDel, nMaxHardRepl=nMaxHardRepl)
        aSugg = oSuggResult.getSuggestions(nSuggLimit)
        if sSfx or sPfx:
            # we add what we removed
            return list(map(lambda sSug: sPfx + sSug + sSfx, aSugg))
        return aSugg

    def _suggest (self, oSuggResult, sRemain, nMaxSwitch=0, nMaxDel=0, nMaxHardRepl=0, nDeep=0, iAddr=0, sNewWord="", bAvoidLoop=False):
        # recursive function
        #logging.info((nDeep * "  ") + sNewWord + ":" + sRemain)
        if not sRemain:
            if int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask:
                oSuggResult.addSugg(sNewWord, nDeep)
            for sTail in self._getTails(iAddr):
                oSuggResult.addSugg(sNewWord+sTail, nDeep)
            return
        cCurrent = sRemain[0:1]
        for cChar, jAddr in self._getCharArcs(iAddr):
            if cChar in cp.d1to1.get(cCurrent, cCurrent):
                self._suggest(oSuggResult, sRemain[1:], nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, jAddr, sNewWord+cChar)
            elif not bAvoidLoop and nMaxHardRepl:
                self._suggest(oSuggResult, sRemain[1:], nMaxSwitch, nMaxDel, nMaxHardRepl-1, nDeep+1, jAddr, sNewWord+cChar, True)
        if not bAvoidLoop: # avoid infinite loop
            if len(sRemain) > 1:
                if cCurrent == sRemain[1:2]:
                    # same char, we remove 1 char without adding 1 to <sNewWord>
                    self._suggest(oSuggResult, sRemain[1:], nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord)
                else:
                    # switching chars
                    if nMaxSwitch:
                        self._suggest(oSuggResult, sRemain[1:2]+sRemain[0:1]+sRemain[2:], nMaxSwitch-1, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True)
                    # delete char
                    if nMaxDel:
                        self._suggest(oSuggResult, sRemain[1:], nMaxSwitch, nMaxDel-1, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True)
                # Phonetic replacements
                for sRepl in cp.get1toXReplacement(sNewWord[-1:], cCurrent, sRemain[1:2]):
                    self._suggest(oSuggResult, sRepl + sRemain[1:], nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True)
                for sRepl in cp.d2toX.get(sRemain[0:2], ()):
                    self._suggest(oSuggResult, sRepl + sRemain[2:], nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True)
            # end of word
            if len(sRemain) == 2:
                for sRepl in cp.dFinal2.get(sRemain, ()):
                    self._suggest(oSuggResult, sRepl, nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True)
            elif len(sRemain) == 1:
                self._suggest(oSuggResult, "", nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True) # remove last char and go on
                for sRepl in cp.dFinal1.get(sRemain, ()):
                    self._suggest(oSuggResult, sRepl, nMaxSwitch, nMaxDel, nMaxHardRepl, nDeep+1, iAddr, sNewWord, True)

    #@timethis
    def suggest2 (self, sWord, nMaxSugg=10):
        "returns a set of suggestions for <sWord>"
        sWord = cp.spellingNormalization(sWord)
        sPfx, sWord, sSfx = cp.cut(sWord)
        oSuggResult = SuggResult(sWord)
        self._suggest2(oSuggResult)
        aSugg = oSuggResult.getSuggestions()
        if sSfx or sPfx:
            # we add what we removed
            return list(map(lambda sSug: sPfx + sSug + sSfx, aSugg))
        return aSugg

    def _suggest2 (self, oSuggResult, nDeep=0, iAddr=0, sNewWord=""):
        # recursive function
        #logging.info((nDeep * "  ") + sNewWord)
        if nDeep >= oSuggResult.nDistLimit:
            sCleanNewWord = cp.simplifyWord(sNewWord)
            if st.distanceSift4(oSuggResult.sCleanWord[:len(sCleanNewWord)], sCleanNewWord) > oSuggResult.nDistLimit:
                return
        if int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask:
            oSuggResult.addSugg(sNewWord, nDeep)
        for cChar, jAddr in self._getCharArcsWithPriority(iAddr, oSuggResult.sWord[nDeep:nDeep+1]):
            self._suggest2(oSuggResult, nDeep+1, jAddr, sNewWord+cChar)
        return

    def _getCharArcs (self, iAddr):
        "generator: yield all chars and addresses from node at address <iAddr>"
        for nVal, jAddr in self._getArcs(iAddr):
            if nVal <= self.nChar:
                yield (self.dCharVal[nVal], jAddr)

    def _getSimilarCharArcs (self, cChar, iAddr):
        "generator: yield similar char of <cChar> and address of the following node"
        for c in cp.d1to1.get(cChar, [cChar]):
            if c in self.dChar:
                jAddr = self._lookupArcNode(self.dChar[c], iAddr)
                if jAddr:
                    yield (c, jAddr)

    def _getCharArcsWithPriority (self, iAddr, cChar):
        if not cChar:
            yield from self._getCharArcs(iAddr)
        lTuple = list(self._getCharArcs(iAddr))
        lTuple.sort(key=lambda t: 0  if t[0] in cp.d1to1.get(cChar, cChar)  else  1)
        yield from lTuple

    def _getTails (self, iAddr, sTail="", n=2):
        "return a list of suffixes ending at a distance of <n> from <iAddr>"
        aTails = set()
        for nVal, jAddr in self._getArcs(iAddr):
            if nVal <= self.nChar:
                if int.from_bytes(self.byDic[jAddr:jAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask:
                    aTails.add(sTail + self.dCharVal[nVal])
                if n and not aTails:
                    aTails.update(self._getTails(jAddr, sTail+self.dCharVal[nVal], n-1))
        return aTails

    def drawPath (self, sWord, iAddr=0):
        "show the path taken by <sWord> in the graph"
        sWord = cp.spellingNormalization(sWord)
        c1 = sWord[0:1]  if sWord  else " "
        iPos = -1
        n = 0
        print(c1 + ": ", end="")
        for c2, jAddr in self._getCharArcs(iAddr):
            print(c2, end="")
            if c2 == sWord[0:1]:
                iNextNodeAddr = jAddr
                iPos = n
            n += 1
        if not sWord:
            return
        if iPos >= 0:
            print("\n   "+ " " * iPos + "|")
            self.drawPath(sWord[1:], iNextNodeAddr)

    def select (self, sPattern=""):
        "generator: returns all entries which morphology fits <sPattern>"
        zPattern = None
        if sPattern:
            try:
                zPattern = re.compile(sPattern)
            except:
                print("# Error in regex pattern")
                traceback.print_exc()
        yield from self._select1(zPattern, 0, "")

    # def morph (self, sWord):
    #     is defined in __init__

    # VERSION 1
    def _select1 (self, zPattern, iAddr, sWord):
        # recursive generator
        for nVal, jAddr in self._getArcs1(iAddr):
            if nVal <= self.nChar:
                # simple character
                yield from self._select1(zPattern, jAddr, sWord + self.lArcVal[nVal])
            else:
                sEntry = sWord + "\t" + self.funcStemming(sWord, self.lArcVal[nVal])
                for nMorphVal, _ in self._getArcs1(jAddr):
                    if not zPattern or zPattern.search(self.lArcVal[nMorphVal]):
                        yield sEntry + "\t" + self.lArcVal[nMorphVal]

    def _morph1 (self, sWord):
        "returns morphologies of <sWord>"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return []
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return []
        if (int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask):
            l = []
            nRawArc = 0
            while not (nRawArc & self._lastArcMask):
                iEndArcAddr = iAddr + self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if nArc > self.nChar:
                    # This value is not a char, this is a stemming code 
                    sStem = ">" + self.funcStemming(sWord, self.lArcVal[nArc])
                    # Now , we go to the next node and retrieve all following arcs values, all of them are tags
                    iAddr2 = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                    nRawArc2 = 0
                    while not (nRawArc2 & self._lastArcMask):
                        iEndArcAddr2 = iAddr2 + self.nBytesArc
                        nRawArc2 = int.from_bytes(self.byDic[iAddr2:iEndArcAddr2], byteorder='big')
                        l.append(sStem + " " + self.lArcVal[nRawArc2 & self._arcMask])
                        iAddr2 = iEndArcAddr2+self.nBytesNodeAddress
                iAddr = iEndArcAddr+self.nBytesNodeAddress
            return l
        return []

    def _stem1 (self, sWord):
        "returns stems list of <sWord>"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return []
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return []
        if (int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask):
            l = []
            nRawArc = 0
            while not (nRawArc & self._lastArcMask):
                iEndArcAddr = iAddr + self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if nArc > self.nChar:
                    # This value is not a char, this is a stemming code 
                    l.append(self.funcStemming(sWord, self.lArcVal[nArc]))
                iAddr = iEndArcAddr+self.nBytesNodeAddress
            return l
        return []

    def _lookupArcNode1 (self, nVal, iAddr):
        "looks if <nVal> is an arc at the node at <iAddr>, if yes, returns address of next node else None"
        while True:
            iEndArcAddr = iAddr+self.nBytesArc
            nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
            if nVal == (nRawArc & self._arcMask):
                # the value we are looking for 
                # we return the address of the next node
                return int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
            else:
                # value not found
                if (nRawArc & self._lastArcMask):
                    return None
                iAddr = iEndArcAddr+self.nBytesNodeAddress

    def _getArcs1 (self, iAddr):
        "generator: return all arcs at <iAddr> as tuples of (nVal, iAddr)"
        while True:
            iEndArcAddr = iAddr+self.nBytesArc
            nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
            yield (nRawArc & self._arcMask, int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big'))
            if (nRawArc & self._lastArcMask):
                break
            iAddr = iEndArcAddr+self.nBytesNodeAddress

    def _writeNodes1 (self, spfDest):
        "for debugging only"
        print(" > Write binary nodes")
        with codecs.open(spfDest, 'w', 'utf-8', newline="\n") as hDst:
            iAddr = 0
            hDst.write("i{:_>10} -- #{:_>10}\n".format("0", iAddr))
            while iAddr < len(self.byDic):
                iEndArcAddr = iAddr+self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                hDst.write("  {:<20}  {:0>16}  i{:>10}   #{:_>10}\n".format(self.lArcVal[nArc], bin(nRawArc)[2:], "?", \
                                                                            int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], \
                                                                                           byteorder='big')))
                iAddr = iEndArcAddr+self.nBytesNodeAddress
                if (nRawArc & self._lastArcMask) and iAddr < len(self.byDic):
                    hDst.write("\ni{:_>10} -- #{:_>10}\n".format("?", iAddr))
            hDst.close()

    # VERSION 2
    def _morph2 (self, sWord):
        "returns morphologies of <sWord>"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return []
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return []
        if (int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask):
            l = []
            nRawArc = 0
            while not (nRawArc & self._lastArcMask):
                iEndArcAddr = iAddr + self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if nArc > self.nChar:
                    # This value is not a char, this is a stemming code 
                    sStem = ">" + self.funcStemming(sWord, self.lArcVal[nArc])
                    # Now , we go to the next node and retrieve all following arcs values, all of them are tags
                    if not (nRawArc & self._addrBitMask):
                        iAddr2 = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                    else:
                        # we go to the end of the node
                        iAddr2 = iEndArcAddr
                        while not (nRawArc & self._lastArcMask):
                            nRawArc = int.from_bytes(self.byDic[iAddr2:iAddr2+self.nBytesArc], byteorder='big')
                            iAddr2 += self.nBytesArc + self.nBytesNodeAddress
                    nRawArc2 = 0
                    while not (nRawArc2 & self._lastArcMask):
                        iEndArcAddr2 = iAddr2 + self.nBytesArc
                        nRawArc2 = int.from_bytes(self.byDic[iAddr2:iEndArcAddr2], byteorder='big')
                        l.append(sStem + " " + self.lArcVal[nRawArc2 & self._arcMask])
                        iAddr2 = iEndArcAddr2+self.nBytesNodeAddress  if not (nRawArc2 & self._addrBitMask) else iEndArcAddr2
                iAddr = iEndArcAddr+self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else iEndArcAddr
            return l
        return []

    def _stem2 (self, sWord):
        "returns stems list of <sWord>"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return []
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return []
        if (int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask):
            l = []
            nRawArc = 0
            while not (nRawArc & self._lastArcMask):
                iEndArcAddr = iAddr + self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if nArc > self.nChar:
                    # This value is not a char, this is a stemming code 
                    l.append(self.funcStemming(sWord, self.lArcVal[nArc]))
                    # Now , we go to the next node
                    if not (nRawArc & self._addrBitMask):
                        iAddr2 = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                    else:
                        # we go to the end of the node
                        iAddr2 = iEndArcAddr
                        while not (nRawArc & self._lastArcMask):
                            nRawArc = int.from_bytes(self.byDic[iAddr2:iAddr2+self.nBytesArc], byteorder='big')
                            iAddr2 += self.nBytesArc + self.nBytesNodeAddress
                iAddr = iEndArcAddr+self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else iEndArcAddr
            return l
        return []

    def _lookupArcNode2 (self, nVal, iAddr):
        "looks if <nVal> is an arc at the node at <iAddr>, if yes, returns address of next node else None"
        while True:
            iEndArcAddr = iAddr+self.nBytesArc
            nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
            if nVal == (nRawArc & self._arcMask):
                # the value we are looking for 
                if not (nRawArc & self._addrBitMask):
                    # we return the address of the next node
                    return int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                else:
                    # we go to the end of the node
                    iAddr = iEndArcAddr
                    while not (nRawArc & self._lastArcMask):
                        nRawArc = int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big')
                        iAddr += self.nBytesArc + self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else self.nBytesArc
                    return iAddr
            else:
                # value not found
                if (nRawArc & self._lastArcMask):
                    return None
                iAddr = iEndArcAddr+self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else iEndArcAddr

    def _writeNodes2 (self, spfDest):
        "for debugging only"
        print(" > Write binary nodes")
        with codecs.open(spfDest, 'w', 'utf-8', newline="\n") as hDst:
            iAddr = 0
            hDst.write("i{:_>10} -- #{:_>10}\n".format("0", iAddr))
            while iAddr < len(self.byDic):
                iEndArcAddr = iAddr+self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if not (nRawArc & self._addrBitMask):
                    iNextNodeAddr = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                    hDst.write("  {:<20}  {:0>16}  i{:>10}   #{:_>10}\n".format(self.lArcVal[nArc], bin(nRawArc)[2:], "?", iNextNodeAddr))
                    iAddr = iEndArcAddr+self.nBytesNodeAddress
                else:
                    hDst.write("  {:<20}  {:0>16}\n".format(self.lArcVal[nArc], bin(nRawArc)[2:]))
                    iAddr = iEndArcAddr
                if (nRawArc & self._lastArcMask):
                    hDst.write("\ni{:_>10} -- #{:_>10}\n".format("?", iAddr))
            hDst.close()

    # VERSION 3
    def _morph3 (self, sWord):
        "returns morphologies of <sWord>"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return []
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return []
        if (int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask):
            l = []
            nRawArc = 0
            iAddrNode = iAddr
            while not (nRawArc & self._lastArcMask):
                iEndArcAddr = iAddr + self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if nArc > self.nChar:
                    # This value is not a char, this is a stemming code 
                    sStem = ">" + self.funcStemming(sWord, self.lArcVal[nArc])
                    # Now , we go to the next node and retrieve all following arcs values, all of them are tags
                    if not (nRawArc & self._addrBitMask):
                        iAddr2 = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                    else:
                        iAddr2 = iAddrNode + int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesOffset], byteorder='big')
                    nRawArc2 = 0
                    while not (nRawArc2 & self._lastArcMask):
                        iEndArcAddr2 = iAddr2 + self.nBytesArc
                        nRawArc2 = int.from_bytes(self.byDic[iAddr2:iEndArcAddr2], byteorder='big')
                        l.append(sStem + " " + self.lArcVal[nRawArc2 & self._arcMask])
                        iAddr2 = iEndArcAddr2+self.nBytesNodeAddress  if not (nRawArc2 & self._addrBitMask) else iEndArcAddr2+self.nBytesOffset
                iAddr = iEndArcAddr+self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else iEndArcAddr+self.nBytesOffset
            return l
        return []

    def _stem3 (self, sWord):
        "returns stems list of <sWord>"
        iAddr = 0
        for c in sWord:
            if c not in self.dChar:
                return []
            iAddr = self._lookupArcNode(self.dChar[c], iAddr)
            if iAddr == None:
                return []
        if (int.from_bytes(self.byDic[iAddr:iAddr+self.nBytesArc], byteorder='big') & self._finalNodeMask):
            l = []
            nRawArc = 0
            iAddrNode = iAddr
            while not (nRawArc & self._lastArcMask):
                iEndArcAddr = iAddr + self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if nArc > self.nChar:
                    # This value is not a char, this is a stemming code 
                    l.append(self.funcStemming(sWord, self.lArcVal[nArc]))
                iAddr = iEndArcAddr+self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else iEndArcAddr+self.nBytesOffset
            return l
        return []

    def _lookupArcNode3 (self, nVal, iAddr):
        "looks if <nVal> is an arc at the node at <iAddr>, if yes, returns address of next node else None"
        iAddrNode = iAddr
        while True:
            iEndArcAddr = iAddr+self.nBytesArc
            nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
            if nVal == (nRawArc & self._arcMask):
                # the value we are looking for 
                if not (nRawArc & self._addrBitMask):
                    return int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                else:
                    return iAddrNode + int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesOffset], byteorder='big')
            else:
                # value not found
                if (nRawArc & self._lastArcMask):
                    return None
                iAddr = iEndArcAddr+self.nBytesNodeAddress  if not (nRawArc & self._addrBitMask)  else iEndArcAddr+self.nBytesOffset

    def _writeNodes3 (self, spfDest):
        "for debugging only"
        print(" > Write binary nodes")
        with codecs.open(spfDest, 'w', 'utf-8', newline="\n") as hDst:
            iAddr = 0
            hDst.write("i{:_>10} -- #{:_>10}\n".format("0", iAddr))
            while iAddr < len(self.byDic):
                iEndArcAddr = iAddr+self.nBytesArc
                nRawArc = int.from_bytes(self.byDic[iAddr:iEndArcAddr], byteorder='big')
                nArc = nRawArc & self._arcMask
                if not (nRawArc & self._addrBitMask):
                    iNextNodeAddr = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesNodeAddress], byteorder='big')
                    hDst.write("  {:<20}  {:0>16}  i{:>10}   #{:_>10}\n".format(self.lArcVal[nArc], bin(nRawArc)[2:], "?", iNextNodeAddr))
                    iAddr = iEndArcAddr+self.nBytesNodeAddress
                else:
                    iNextNodeAddr = int.from_bytes(self.byDic[iEndArcAddr:iEndArcAddr+self.nBytesOffset], byteorder='big')
                    hDst.write("  {:<20}  {:0>16}  i{:>10}   +{:_>10}\n".format(self.lArcVal[nArc], bin(nRawArc)[2:], "?", iNextNodeAddr))
                    iAddr = iEndArcAddr+self.nBytesOffset
                if (nRawArc & self._lastArcMask):
                    hDst.write("\ni{:_>10} -- #{:_>10}\n".format("?", iAddr))
            hDst.close()
