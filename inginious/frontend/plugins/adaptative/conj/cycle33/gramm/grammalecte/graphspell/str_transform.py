#!python3


#### DISTANCE CALCULATIONS

def longestCommonSubstring (s1, s2):
    # http://en.wikipedia.org/wiki/Longest_common_substring_problem
    # http://en.wikibooks.org/wiki/Algorithm_implementation/Strings/Longest_common_substring
    M = [ [0]*(1+len(s2)) for i in range(1+len(s1)) ]
    longest, x_longest = 0, 0
    for x in range(1, 1+len(s1)):
        for y in range(1, 1+len(s2)):
            if s1[x-1] == s2[y-1]:
                M[x][y] = M[x-1][y-1] + 1
                if M[x][y] > longest:
                    longest = M[x][y]
                    x_longest = x
            else:
                M[x][y] = 0
    return s1[x_longest-longest : x_longest]


def distanceDamerauLevenshtein (s1, s2):
    "distance of Damerau-Levenshtein between <s1> and <s2>"
    # https://fr.wikipedia.org/wiki/Distance_de_Damerau-Levenshtein
    d = {}
    nLen1 = len(s1)
    nLen2 = len(s2)
    for i in range(-1, nLen1+1):
        d[i, -1] = i + 1
    for j in range(-1, nLen2+1):
        d[-1, j] = j + 1
    for i in range(nLen1):
        for j in range(nLen2):
            nCost = 0  if s1[i] == s2[j]  else 1
            d[i, j] = min(
                d[i-1, j]   + 1,        # Deletion
                d[i,   j-1] + 1,        # Insertion
                d[i-1, j-1] + nCost,    # Substitution
            )
            if i and j and s1[i] == s2[j-1] and s1[i-1] == s2[j]:
                d[i, j] = min(d[i, j], d[i-2, j-2] + nCost)     # Transposition
    return d[nLen1-1, nLen2-1]


def distanceSift4 (s1, s2, nMaxOffset=5):
    "implementation of general Sift4."
    # https://siderite.blogspot.com/2014/11/super-fast-and-accurate-string-distance.html
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    nLen1, nLen2 = len(s1), len(s2)
    i1, i2 = 0, 0   # Cursors for each string
    nLargestCS = 0  # Largest common substring
    nLocalCS = 0    # Local common substring
    nTrans = 0      # Number of transpositions ('ab' vs 'ba')
    lOffset = []    # Offset pair array, for computing the transpositions
 
    while i1 < nLen1 and i2 < nLen2:
        if s1[i1] == s2[i2]:
            nLocalCS += 1
            # Check if current match is a transposition
            bTrans = False
            i = 0
            while i < len(lOffset):
                t = lOffset[i]
                if i1 <= t[0] or i2 <= t[1]:
                    bTrans = abs(i2-i1) >= abs(t[1] - t[0])
                    if bTrans:
                        nTrans += 1
                    elif not t[2]:
                        t[2] = True
                        nTrans += 1
                    break
                elif i1 > t[1] and i2 > t[0]:
                    del lOffset[i]
                else:
                    i += 1
            lOffset.append([i1, i2, bTrans])
        else:
            nLargestCS += nLocalCS
            nLocalCS = 0
            if i1 != i2:
                i1 = i2 = min(i1, i2)
            for i in range(nMaxOffset):
                if i1 + i >= nLen1 and i2 + i >= nLen2:
                    break
                elif i1 + i < nLen1 and s1[i1+i] == s2[i2]:
                    i1 += i - 1
                    i2 -= 1
                    break
                elif i2 + i < nLen2 and s1[i1] == s2[i2+i]:
                    i2 += i - 1
                    i1 -= 1
                    break
        i1 += 1
        i2 += 1
        if i1 >= nLen1 or i2 >= nLen2:
            nLargestCS += nLocalCS
            nLocalCS = 0
            i1 = i2 = min(i1, i2)
    nLargestCS += nLocalCS
    return round(max(nLen1, nLen2) - nLargestCS + nTrans)


def showDistance (s1, s2):
    print("Damerau-Levenshtein: " + s1 + "/" + s2 + " = " + distanceDamerauLevenshtein(s1, s2))
    print("Sift4:" + s1 + "/" + s2 + " = " + distanceSift4(s1, s2))




#### STEMMING OPERATIONS

## No stemming

def noStemming (sFlex, sStem):
    return sStem

def rebuildWord (sFlex, cmd1, cmd2):
    if cmd1 == "_":
        return sFlex
    n, c = cmd1.split(":")
    s = s[:n] + c + s[n:]
    if cmd2 == "_":
        return s
    n, c = cmd2.split(":")
    return s[:n] + c + s[n:]

    
## Define affixes for stemming

# Note: 48 is the ASCII code for "0"


# Suffix only
def defineSuffixCode (sFlex, sStem):
    """ Returns a string defining how to get stem from flexion
            "n(sfx)"
        with n: a char with numeric meaning, "0" = 0, "1" = 1, ... ":" = 10, etc. (See ASCII table.) Says how many letters to strip from flexion.
             sfx [optional]: string to add on flexion
        Examples:
            "0": strips nothing, adds nothing
            "1er": strips 1 letter, adds "er"
            "2": strips 2 letters, adds nothing
    """
    if sFlex == sStem:
        return "0"
    jSfx = 0
    for i in range(min(len(sFlex), len(sStem))):
        if sFlex[i] != sStem[i]:
            break
        jSfx += 1
    return chr(len(sFlex)-jSfx+48) + sStem[jSfx:]  


def changeWordWithSuffixCode (sWord, sSfxCode):
    if sSfxCode == "0":
        return sWord
    return sWord[:-(ord(sSfxCode[0])-48)] + sSfxCode[1:]  if sSfxCode[0] != '0'  else sWord + sSfxCode[1:]


# Prefix and suffix

def defineAffixCode (sFlex, sStem):
    """ Returns a string defining how to get stem from flexion. Examples:
            "0" if stem = flexion
            "stem" if no common substring
            "n(pfx)/m(sfx)"
        with n and m: chars with numeric meaning, "0" = 0, "1" = 1, ... ":" = 10, etc. (See ASCII table.) Says how many letters to strip from flexion.
            pfx [optional]: string to add before the flexion 
            sfx [optional]: string to add after the flexion
    """
    if sFlex == sStem:
        return "0"
    # is stem a substring of flexion?
    n = sFlex.find(sStem)
    if n >= 0:
        return "{}/{}".format(chr(n+48), chr(len(sFlex)-(len(sStem)+n)+48))
    # no, so we are looking for common substring
    sSubs = longestCommonSubstring(sFlex, sStem)
    if len(sSubs) > 1:
        iPos = sStem.find(sSubs)
        sPfx = sStem[:iPos]
        sSfx = sStem[iPos+len(sSubs):]
        n = sFlex.find(sSubs)
        m = len(sFlex) - (len(sSubs)+n)
        return chr(n+48) + sPfx + "/" + chr(m+48) + sSfx
    return sStem


def changeWordWithAffixCode (sWord, sAffCode):
    if sAffCode == "0":
        return sWord
    if '/' not in sAffCode:
        return sAffCode
    sPfxCode, sSfxCode = sAffCode.split('/')
    sWord = sPfxCode[1:] + sWord[(ord(sPfxCode[0])-48):] 
    return sWord[:-(ord(sSfxCode[0])-48)] + sSfxCode[1:]  if sSfxCode[0] != '0'  else sWord + sSfxCode[1:]

