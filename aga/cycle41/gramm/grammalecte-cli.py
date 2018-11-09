#!/usr/bin/env python3

import sys
import os.path
import argparse
import json

import grammalecte
import grammalecte.text as txt
from grammalecte.graphspell.echo import echo


_EXAMPLE = "Quoi ? Racontes ! Racontes-moi ! Bon sangg, parles ! Oui. Il y a des menteur partout. " \
           "Je suit sidéré par la brutales arrogance de cette homme-là. Quelle salopard ! Un escrocs de la pire espece. " \
           "Quant sera t’il châtiés pour ses mensonge ?             Merde ! J’en aie marre."

_HELP = """
    /help                       /h      show this text
    ?word1 [word2] ...                  words analysis
    !word                               suggestion
    >word                               draw path of word in the word graph
    =filter                             show all entries whose morphology fits to filter
    /lopt                       /lo     list options
    /+ option1 [option2] ...            activate grammar checking options
    /- option1 [option2] ...            deactivate grammar checking options
    /lrules [pattern]           /lr     list rules
    /--rule1 [rule2] ...                deactivate grammar checking rule
    /++rule1 [rule2] ...                reactivate grammar checking rule
    /quit                       /q      exit
"""


def _getText (sInputText):
    sText = input(sInputText)
    if sText == "*":
        return _EXAMPLE
    if sys.platform == "win32":
        # Apparently, the console transforms «’» in «'».
        # So we reverse it to avoid many useless warnings.
        sText = sText.replace("'", "’")
    return sText


def readFile (spf):
    "generator: returns file line by line"
    if os.path.isfile(spf):
        with open(spf, "r", encoding="utf-8") as hSrc:
            for sLine in hSrc:
                yield sLine
    else:
        print("# Error: file <" + spf + ">not found.")


def generateParagraphFromFile (spf, bConcatLines=False):
    "generator: returns text by tuple of (iParagraph, sParagraph, lLineSet)"
    if not bConcatLines:
        for iParagraph, sLine in enumerate(readFile(spf), 1):
            yield iParagraph, sLine, None
    else:
        lLine = []
        iParagraph = 1
        for iLine, sLine in enumerate(readFile(spf), 1):
            if sLine.strip():
                lLine.append((iLine, sLine))
            elif lLine:
                sText, lLineSet = txt.createParagraphWithLines(lLine)
                yield iParagraph, sText, lLineSet
                lLine = []
            iParagraph += 1
        if lLine:
            sText, lLineSet = txt.createParagraphWithLines(lLine)
            yield iParagraph, sText, lLineSet


def output (sText, hDst=None):
    if not hDst:
        echo(sText, end="")
    else:
        hDst.write(sText)


def main ():
    xParser = argparse.ArgumentParser()
    xParser.add_argument("-f", "--file", help="parse file (UTF-8 required!) [on Windows, -f is similar to -ff]", type=str)
    xParser.add_argument("-ff", "--file_to_file", help="parse file (UTF-8 required!) and create a result file (*.res.txt)", type=str)
    xParser.add_argument("-owe", "--only_when_errors", help="display results only when there are errors", action="store_true")
    xParser.add_argument("-j", "--json", help="generate list of errors in JSON (only with option --file or --file_to_file)", action="store_true")
    xParser.add_argument("-cl", "--concat_lines", help="concatenate lines not separated by an empty paragraph (only with option --file or --file_to_file)", action="store_true")
    xParser.add_argument("-tf", "--textformatter", help="auto-format text according to typographical rules (not with option --concat_lines)", action="store_true")
    xParser.add_argument("-tfo", "--textformatteronly", help="auto-format text and disable grammar checking (only with option --file or --file_to_file)", action="store_true")
    xParser.add_argument("-ctx", "--context", help="return errors with context (only with option --json)", action="store_true")
    xParser.add_argument("-wss", "--with_spell_sugg", help="add suggestions for spelling errors (only with option --file or --file_to_file)", action="store_true")
    xParser.add_argument("-w", "--width", help="width in characters (40 < width < 200; default: 100)", type=int, choices=range(40,201,10), default=100)
    xParser.add_argument("-lo", "--list_options", help="list options", action="store_true")
    xParser.add_argument("-lr", "--list_rules", nargs="?", help="list rules [regex pattern as filter]", const="*")
    xParser.add_argument("-sug", "--suggest", help="get suggestions list for given word", type=str)
    xParser.add_argument("-on", "--opt_on", nargs="+", help="activate options")
    xParser.add_argument("-off", "--opt_off", nargs="+", help="deactivate options")
    xParser.add_argument("-roff", "--rule_off", nargs="+", help="deactivate rules")
    xParser.add_argument("-d", "--debug", help="debugging mode (only in interactive mode)", action="store_true")
    xArgs = xParser.parse_args()

    oGrammarChecker = grammalecte.GrammarChecker("fr")
    oSpellChecker = oGrammarChecker.getSpellChecker()
    oLexicographer = oGrammarChecker.getLexicographer()
    oTextFormatter = oGrammarChecker.getTextFormatter()

    if not xArgs.json:
        echo("Grammalecte v{}".format(oGrammarChecker.gce.version))

    # list options or rules
    if xArgs.list_options or xArgs.list_rules:
        if xArgs.list_options:
            oGrammarChecker.gce.displayOptions("fr")
        if xArgs.list_rules:
            oGrammarChecker.gce.displayRules(None  if xArgs.list_rules == "*"  else xArgs.list_rules)
        exit()

    # spell suggestions
    if xArgs.suggest:
        for lSugg in oSpellChecker.suggest(xArgs.suggest):
            if xArgs.json:
                sText = json.dumps({ "aSuggestions": lSugg }, ensure_ascii=False)
            else:
                sText = "Suggestions : " + " | ".join(lSugg)
            echo(sText)
        exit()

    # disable options
    if not xArgs.json:
        xArgs.context = False
    if xArgs.concat_lines:
        xArgs.textformatter = False

    # grammar options
    oGrammarChecker.gce.setOptions({"html": True, "latex": True})
    if xArgs.opt_on:
        oGrammarChecker.gce.setOptions({ opt:True  for opt in xArgs.opt_on  if opt in oGrammarChecker.gce.getOptions() })
    if xArgs.opt_off:
        oGrammarChecker.gce.setOptions({ opt:False  for opt in xArgs.opt_off  if opt in oGrammarChecker.gce.getOptions() })

    # disable grammar rules
    if xArgs.rule_off:
        for sRule in xArgs.rule_off:
            oGrammarChecker.gce.ignoreRule(sRule)

    sFile = xArgs.file or xArgs.file_to_file
    if sFile:
        # file processing
        hDst = open(sFile[:sFile.rfind(".")]+".res.txt", "w", encoding="utf-8", newline="\n")  if xArgs.file_to_file or sys.platform == "win32"  else None
        bComma = False
        if xArgs.json:
            output('{ "grammalecte": "'+oGrammarChecker.gce.version+'", "lang": "'+oGrammarChecker.gce.lang+'", "data" : [\n', hDst)
        for i, sText, lLineSet in generateParagraphFromFile(sFile, xArgs.concat_lines):
            if xArgs.textformatter or xArgs.textformatteronly:
                sText = oTextFormatter.formatText(sText)
            if xArgs.textformatteronly:
                output(sText, hDst)
                continue
            if xArgs.json:
                sText = oGrammarChecker.generateParagraphAsJSON(i, sText, bContext=xArgs.context, bEmptyIfNoErrors=xArgs.only_when_errors, \
                                                                bSpellSugg=xArgs.with_spell_sugg, bReturnText=xArgs.textformatter, lLineSet=lLineSet)
            else:
                sText = oGrammarChecker.generateParagraph(sText, bEmptyIfNoErrors=xArgs.only_when_errors, bSpellSugg=xArgs.with_spell_sugg, nWidth=xArgs.width)
            if sText:
                if xArgs.json and bComma:
                    output(",\n", hDst)
                output(sText, hDst)
                bComma = True
            if hDst:
                echo("§ %d\r" % i, end="", flush=True)
        if xArgs.json:
            output("\n]}\n", hDst)
    else:
        # pseudo-console
        sInputText = "\n~==========~ Enter your text [/h /q] ~==========~\n"
        sText = _getText(sInputText)
        while True:
            if sText.startswith("?"):
                for sWord in sText[1:].strip().split():
                    if sWord:
                        echo("* " + sWord)
                        for sMorph in oSpellChecker.getMorph(sWord):
                            echo("  {:<32} {}".format(sMorph, oLexicographer.formatTags(sMorph)))
            elif sText.startswith("!"):
                for sWord in sText[1:].strip().split():
                    if sWord:
                        for lSugg in oSpellChecker.suggest(sWord):
                            echo(" | ".join(lSugg))
            elif sText.startswith(">"):
                oSpellChecker.drawPath(sText[1:].strip())
            elif sText.startswith("="):
                for sRes in oSpellChecker.select(sText[1:].strip()):
                    echo(sRes)
            elif sText.startswith("/+ "):
                oGrammarChecker.gce.setOptions({ opt:True  for opt in sText[3:].strip().split()  if opt in oGrammarChecker.gce.getOptions() })
                echo("done")
            elif sText.startswith("/- "):
                oGrammarChecker.gce.setOptions({ opt:False  for opt in sText[3:].strip().split()  if opt in oGrammarChecker.gce.getOptions() })
                echo("done")
            elif sText.startswith("/-- "):
                for sRule in sText[3:].strip().split():
                    oGrammarChecker.gce.ignoreRule(sRule)
                echo("done")
            elif sText.startswith("/++ "):
                for sRule in sText[3:].strip().split():
                    oGrammarChecker.gce.reactivateRule(sRule)
                echo("done")
            elif sText == "/debug" or sText == "/d":
                xArgs.debug = not(xArgs.debug)
                echo("debug mode on"  if xArgs.debug  else "debug mode off")
            elif sText == "/textformatter" or sText == "/tf":
                xArgs.textformatter = not(xArgs.textformatter)
                echo("textformatter on"  if xArgs.debug  else "textformatter off")
            elif sText == "/help" or sText == "/h":
                echo(_HELP)
            elif sText == "/lopt" or sText == "/lo":
                oGrammarChecker.gce.displayOptions("fr")
            elif sText.startswith("/lr"):
                sText = sText.strip()
                sFilter = sText[sText.find(" "):].strip()  if sText != "/lr" and sText != "/rules"  else None
                oGrammarChecker.gce.displayRules(sFilter)
            elif sText == "/quit" or sText == "/q":
                break
            elif sText.startswith("/rl"):
                # reload (todo)
                pass
            else:
                for sParagraph in txt.getParagraph(sText):
                    if xArgs.textformatter:
                        sText = oTextFormatter.formatText(sText)
                    sRes = oGrammarChecker.generateParagraph(sText, bEmptyIfNoErrors=xArgs.only_when_errors, nWidth=xArgs.width, bDebug=xArgs.debug)
                    if sRes:
                        echo("\n" + sRes)
                    else:
                        echo("\nNo error found.")
            sText = _getText(sInputText)


if __name__ == '__main__':
    main()
