# Masculins, féminins, singuliers et pluriels

from .mfsp_data import lTagMiscPlur as _lTagMiscPlur
from .mfsp_data import lTagMasForm as _lTagMasForm
from .mfsp_data import dMiscPlur as _dMiscPlur
from .mfsp_data import dMasForm as _dMasForm


def isFemForm (sWord):
    "returns True if sWord exists in _dMasForm"
    return sWord in _dMasForm

def getMasForm (sWord, bPlur):
    "returns masculine form with feminine form"
    if sWord in _dMasForm:
        return [ _modifyStringWithSuffixCode(sWord, sTag)  for sTag in _whatSuffixCodes(sWord, bPlur) ]
    return []

def hasMiscPlural (sWord):
    "returns True if sWord exists in dPlurMisc"
    return sWord in _dMiscPlur

def getMiscPlural (sWord):
    "returns plural form with singular form"
    if sWord in _dMiscPlur:
        return [ _modifyStringWithSuffixCode(sWord, sTag)  for sTag in _lTagMiscPlur[_dMiscPlur[sWord]].split("|") ]
    return []

def _whatSuffixCodes (sWord, bPlur):
    "necessary only for dMasFrom"
    sSfx = _lTagMasForm[_dMasForm[sWord]]
    if "/" in sSfx:
        if bPlur:
            return sSfx[sSfx.find("/")+1:].split("|")
        return sSfx[:sSfx.find("/")].split("|")
    return sSfx.split("|")

def _modifyStringWithSuffixCode (sWord, sSfx):
    "returns sWord modified by sSfx"
    if not sSfx:
        return ""
    if sSfx == "0":
        return sWord
    try:
        return sWord[:-(ord(sSfx[0])-48)] + sSfx[1:]  if sSfx[0] != '0'  else  sWord + sSfx[1:]  # 48 is the ASCII code for "0"
    except:
        return "## erreur, code : " + str(sSfx) + " ##"
