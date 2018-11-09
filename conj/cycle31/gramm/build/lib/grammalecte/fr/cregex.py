# Grammalecte - Compiled regular expressions

import re

#### Lemme
Lemma = re.compile("^>(\w[\w-]*)")

#### Analyses
Gender = re.compile(":[mfe]")
Number = re.compile(":[spi]")

#### Nom et adjectif
NA = re.compile(":[NA]")

## nombre
NAs = re.compile(":[NA].*:s")
NAp = re.compile(":[NA].*:p")
NAi = re.compile(":[NA].*:i")
NAsi = re.compile(":[NA].*:[si]")
NApi = re.compile(":[NA].*:[pi]")

## genre
NAm = re.compile(":[NA].*:m")
NAf = re.compile(":[NA].*:f")
NAe = re.compile(":[NA].*:e")
NAme = re.compile(":[NA].*:[me]")
NAfe = re.compile(":[NA].*:[fe]")

## nombre et genre
# singuilier
NAms = re.compile(":[NA].*:m.*:s")
NAfs = re.compile(":[NA].*:f.*:s")
NAes = re.compile(":[NA].*:e.*:s")
NAmes = re.compile(":[NA].*:[me].*:s")
NAfes = re.compile(":[NA].*:[fe].*:s")

# singulier et invariable
NAmsi = re.compile(":[NA].*:m.*:[si]")
NAfsi = re.compile(":[NA].*:f.*:[si]")
NAesi = re.compile(":[NA].*:e.*:[si]")
NAmesi = re.compile(":[NA].*:[me].*:[si]")
NAfesi = re.compile(":[NA].*:[fe].*:[si]")

# pluriel
NAmp = re.compile(":[NA].*:m.*:p")
NAfp = re.compile(":[NA].*:f.*:p")
NAep = re.compile(":[NA].*:e.*:p")
NAmep = re.compile(":[NA].*:[me].*:p")
NAfep = re.compile(":[NA].*:[me].*:p")

# pluriel et invariable
NAmpi = re.compile(":[NA].*:m.*:[pi]")
NAfpi = re.compile(":[NA].*:f.*:[pi]")
NAepi = re.compile(":[NA].*:e.*:[pi]")
NAmepi = re.compile(":[NA].*:[me].*:[pi]")
NAfepi = re.compile(":[NA].*:[fe].*:[pi]")

# divers
AD = re.compile(":[AB]")

#### Verbe
Vconj = re.compile(":[123][sp]")
Vconj123 = re.compile(":V[123].*:[123][sp]")

#### Nom | Adjectif | Verbe
NVconj = re.compile(":(?:N|[123][sp])")
NAVconj = re.compile(":(?:N|A|[123][sp])")

#### Spécifique
NnotA = re.compile(":N(?!:A)")
PNnotA = re.compile(":(?:N(?!:A)|Q)")

#### Noms propres
NP = re.compile(":(?:M[12P]|T)")
NPm = re.compile(":(?:M[12P]|T):m")
NPf = re.compile(":(?:M[12P]|T):f")
NPe = re.compile(":(?:M[12P]|T):e")


#### FONCTIONS

def getLemmaOfMorph (s):
    return Lemma.search(s).group(1)

def checkAgreement (l1, l2):
    # check number agreement
    if not mbInv(l1) and not mbInv(l2):
        if mbSg(l1) and not mbSg(l2):
            return False
        if mbPl(l1) and not mbPl(l2):
            return False
    # check gender agreement
    if mbEpi(l1) or mbEpi(l2):
        return True
    if mbMas(l1) and not mbMas(l2):
        return False
    if mbFem(l1) and not mbFem(l2):
        return False
    return True

def checkConjVerb (lMorph, sReqConj):
    return any(sReqConj in s  for s in lMorph)

def getGender (lMorph):
    "returns gender of word (':m', ':f', ':e' or empty string)."
    sGender = ""
    for sMorph in lMorph:
        m = Gender.search(sMorph)
        if m:
            if not sGender:
                sGender = m.group(0)
            elif sGender != m.group(0):
                return ":e"
    return sGender

def getNumber (lMorph):
    "returns number of word (':s', ':p', ':i' or empty string)."
    sNumber = ""
    for sMorph in lMorph:
        m = Number.search(sWord)
        if m:
            if not sNumber:
                sNumber = m.group(0)
            elif sNumber != m.group(0):
                return ":i"
    return sNumber

# NOTE :  isWhat (lMorph)    returns True   if lMorph contains nothing else than What
#         mbWhat (lMorph)    returns True   if lMorph contains What at least once

## isXXX = it’s certain

def isNom (lMorph):
    return all(":N" in s  for s in lMorph)

def isNomNotAdj (lMorph):
    return all(NnotA.search(s)  for s in lMorph)

def isAdj (lMorph):
    return all(":A" in s  for s in lMorph)

def isNomAdj (lMorph):
    return all(NA.search(s)  for s in lMorph)

def isNomVconj (lMorph):
    return all(NVconj.search(s)  for s in lMorph)

def isInv (lMorph):
    return all(":i" in s  for s in lMorph)

def isSg (lMorph):
    return all(":s" in s  for s in lMorph)

def isPl (lMorph):
    return all(":p" in s  for s in lMorph)

def isEpi (lMorph):
    return all(":e" in s  for s in lMorph)

def isMas (lMorph):
    return all(":m" in s  for s in lMorph)

def isFem (lMorph):
    return all(":f" in s  for s in lMorph)


## mbXXX = MAYBE XXX

def mbNom (lMorph):
    return any(":N" in s  for s in lMorph)

def mbAdj (lMorph):
    return any(":A" in s  for s in lMorph)

def mbAdjNb (lMorph):
    return any(AD.search(s)  for s in lMorph)

def mbNomAdj (lMorph):
    return any(NA.search(s)  for s in lMorph)

def mbNomNotAdj (lMorph):
    b = False
    for s in lMorph:
        if ":A" in s:
            return False
        if ":N" in s:
            b = True
    return b

def mbPpasNomNotAdj (lMorph):
    return any(PNnotA.search(s)  for s in lMorph)

def mbVconj (lMorph):
    return any(Vconj.search(s)  for s in lMorph)

def mbVconj123 (lMorph):
    return any(Vconj123.search(s)  for s in lMorph)

def mbMG (lMorph):
    return any(":G" in s  for s in lMorph)

def mbInv (lMorph):
    return any(":i" in s  for s in lMorph)

def mbSg (lMorph):
    return any(":s" in s  for s in lMorph)

def mbPl (lMorph):
    return any(":p" in s  for s in lMorph)

def mbEpi (lMorph):
    return any(":e" in s  for s in lMorph)

def mbMas (lMorph):
    return any(":m" in s  for s in lMorph)

def mbFem (lMorph):
    return any(":f" in s  for s in lMorph)

def mbNpr (lMorph):
    return any(NP.search(s)  for s in lMorph)

def mbNprMasNotFem (lMorph):
    if any(NPf.search(s)  for s in lMorph):
        return False
    return any(NPm.search(s)  for s in lMorph)
