#!python3

import textwrap
from itertools import chain


def getParagraph (sText):
    "generator: returns paragraphs of text"
    iStart = 0
    sText = sText.replace("\r\n", "\n").replace("\r", "\n")
    iEnd = sText.find("\n", iStart)
    while iEnd != -1:
        yield sText[iStart:iEnd]
        iStart = iEnd + 1
        iEnd = sText.find("\n", iStart)
    yield sText[iStart:]


def wrap (sText, nWidth=80):
    "generator: returns text line by line"
    sText = sText.rstrip("\r\n")
    while sText:
        if len(sText) > nWidth:
            nEnd = sText.rfind(" ", 0, nWidth) + 1
            if nEnd > 0:
                yield sText[0:nEnd]
                sText = sText[nEnd:]
            else:
                yield sText[0:nWidth]
                sText = sText[nWidth:]
        else:
            break
    yield sText


def generateParagraph (sParagraph, aGrammErrs, aSpellErrs, nWidth=100):
    "Returns a text with readable errors"
    if not sParagraph:
        return ""
    lGrammErrs = sorted(aGrammErrs, key=lambda d: d["nStart"])
    lSpellErrs = sorted(aSpellErrs, key=lambda d: d['nStart'])
    sText = ""
    nOffset = 0
    for sLine in wrap(sParagraph, nWidth): # textwrap.wrap(sParagraph, nWidth, drop_whitespace=False)
        sText += sLine + "\n"
        ln = len(sLine)
        sErrLine = ""
        nLenErrLine = 0
        nGrammErr = 0
        nSpellErr = 0
        for dErr in lGrammErrs:
            nStart = dErr["nStart"] - nOffset
            if nStart < ln:
                nGrammErr += 1
                if nStart >= nLenErrLine:
                    sErrLine += " " * (nStart - nLenErrLine) + "^" * (dErr["nEnd"] - dErr["nStart"])
                    nLenErrLine = len(sErrLine)
            else:
                break
        for dErr in lSpellErrs:
            nStart = dErr['nStart'] - nOffset
            if nStart < ln:
                nSpellErr += 1
                nEnd = dErr['nEnd'] - nOffset
                if nEnd > len(sErrLine):
                    sErrLine += " " * (nEnd - len(sErrLine))
                sErrLine = sErrLine[:nStart] + "°" * (nEnd - nStart) + sErrLine[nEnd:]
            else:
                break
        if sErrLine:
            sText += sErrLine + "\n"
        if nGrammErr:
            sText += getReadableErrors(lGrammErrs[:nGrammErr], nWidth)
            del lGrammErrs[0:nGrammErr]
        if nSpellErr:
            sText += getReadableErrors(lSpellErrs[:nSpellErr], nWidth, True)
            del lSpellErrs[0:nSpellErr]
        nOffset += ln
    return sText


def getReadableErrors (lErrs, nWidth, bSpell=False):
    "Returns lErrs errors as readable errors"
    sErrors = ""
    for dErr in lErrs:
        if not bSpell or "aSuggestions" in dErr:
            sMsg, *others = getReadableError(dErr, bSpell).split("\n")
            sErrors += "\n".join(textwrap.wrap(sMsg, nWidth, subsequent_indent="  ")) + "\n"
            for arg in others:
                sErrors += "\n".join(textwrap.wrap(arg, nWidth, subsequent_indent="    ")) + "\n"
    if sErrors != "":
        sErrors += "\n"
    return sErrors


def getReadableError (dErr, bSpell=False):
    "Returns an error dErr as a readable error"
    try:
        if bSpell:
            s = u"* {nStart}:{nEnd}  # {sValue}:".format(**dErr)
        else:
            s = u"* {nStart}:{nEnd}  # {sLineId} / {sRuleId}:\n".format(**dErr)
            s += "  " + dErr.get("sMessage", "# error : message not found")
        if dErr.get("aSuggestions", None):
            s += "\n  > Suggestions : " + " | ".join(dErr.get("aSuggestions", "# error : suggestions not found"))
        if dErr.get("URL", None):
            s += "\n  > URL: " + dErr["URL"]
        return s
    except KeyError:
        return u"* Non-compliant error: {}".format(dErr)


def createParagraphWithLines (lLine):
    "Returns a text as merged lines and a set of data about lines (line_number_y, start_x, end_x)"
    sText = ""
    lLineSet = []
    nLine = 1
    n = 0
    for iLineNumber, sLine in lLine:
        sLine = sLine.rstrip("\r\n")
        if nLine < len(lLine) and not sLine.endswith((" ", " ", "-", "–", "—")):
            sLine += " "
        lLineSet.append((iLineNumber, n, n + len(sLine)))
        n += len(sLine)
        sText += sLine
        nLine += 1
    return sText, lLineSet


def convertToXY (aGrammErrs, aSpellErrs, lLineSet):
    """Converts errors position as an y and x position in a text (y is line number, x is row number).
       lLineSet is a list of sets (line_number_y, start_x, end_x) describing how the paragraph is divided."""
    for dErr in chain(aGrammErrs, aSpellErrs):
        for i, elem in enumerate(lLineSet, 1):
            if dErr['nEnd'] <= elem[2]:
                dErr['nEndY'] = elem[0]
                dErr['nEndX'] = dErr['nEnd'] - elem[1]
                break
        for elem in reversed(lLineSet[:i]):
            if dErr['nStart'] >= elem[1]:
                dErr['nStartY'] = elem[0]
                dErr['nStartX'] = dErr['nStart'] - elem[1]
                break
        del dErr['nStart']
        del dErr['nEnd']
    return aGrammErrs, aSpellErrs
