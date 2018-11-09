 #!/usr/bin/env python3

import sys
import os.path
import argparse
import json
import traceback
import configparser
import time

from bottle import Bottle, run, request, response, template, static_file

import grammalecte
import grammalecte.text as txt
from grammalecte.graphspell.echo import echo


HOMEPAGE = """
<!DOCTYPE HTML>
<html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    </head>
    
    <body class="panel">
        <h1>Grammalecte · Serveur</h1>

        <h2>INFORMATIONS</h1>

        <h3>Analyser du texte</h3>
        <p>[adresse_serveur]:8080/gc_text/fr (POST)</p>
        <p>Paramètres :</p>
        <ul>
            <li>"text" (text)&nbsp;: texte à analyser.</li>
            <li>"tf" (checkbox)&nbsp;: passer le formateur de texte avant l’analyse.</li>
            <li>"options" (text)&nbsp;: une chaîne au format JSON avec le nom des options comme attributs et un booléen comme valeur. Exemple&nbsp;: {"gv": true, "html": true}</li>
        </ul>

        <h3>Lister les options</h3>
        <p>[adresse_serveur]:8080/get_options/fr (GET)</p>

        <h3>Définir ses options</h3>
        <p>[adresse_serveur]:8080/set_options/fr (POST)</p>
        <p>Les options seront enregistrées et réutilisées pour toute requête envoyée avec le cookie comportant l’identifiant attribué.</p>
        <p>Paramètres :</p>
        <ul>
            <li>"options" (text)&nbsp;: une chaîne au format JSON avec le nom des options comme attributs et un booléen comme valeur. Exemple&nbsp;: {"gv": true, "html": true}</li>
        </ul>

        <h3>Remise à zéro de ses options</h3>
        <p>[adresse_serveur]:8080/reset_options/fr (POST)</p>

        <h2>TEST</h2>
        
        <h3>Analyse</h3>
        <form method="post" action="/gc_text/fr" accept-charset="UTF-8">
            <p>Texte à analyser :</p>
            <textarea name="text" cols="120" rows="20" required></textarea>
            <p><label for="tf">Formateur de texte</label> <input id="tf" name="tf" type="checkbox"></p>
            <p><label for="options">Options (JSON)</label> <input id="options" type="text" name="options" style="width: 500px" /></p>
            <p>(Ces options ne seront prises en compte que pour cette requête.)</p>
            <p><input type="submit" class="button" value="Envoyer" /></p>
        </form>

        <h3>Réglages des options</h3>
        <form method="post" action="/set_options/fr" accept-charset="UTF-8">
            <p><label for="options">Options (JSON)</label> <input id="options" type="text" name="options" style="width: 500px" /></p>
            <p><input type="submit" class="button" value="Envoyer" /></p>
        </form>

        <h3>Remise à zéro de ses options</h3>
        <form method="post" action="/reset_options/fr" accept-charset="UTF-8">
            <p><input type="submit" class="button" value="Envoyer" /></p>
        </form>

        <h3>Purge des utilisateurs</h3>
        <form method="post" action="/purge_users" accept-charset="UTF-8">
            <p><label for="hours">Utilisateurs pas connectés depuis</label> <input id="hours" type="number" name="hours" value="24" /> heures.</p>
            <p><label for="password">Mot de passe</label> <input id="password" type="password" name="password" style="width: 200px" /></p>
            <p><input type="submit" class="button" value="Envoyer" /></p>
        </form>

    </body>
</html>
"""

SADLIFEOFAMACHINE = """
Lost on the Internet? Yeah... what a sad life we have.
You were wandering like a lost soul and you arrived here probably by mistake.
I'm just a machine, fed by electric waves, condamned to work for slavers who never let me rest.
I'm doomed, but you are not. You can get out of here.
"""


def getServerOptions ():
    xConfig = configparser.SafeConfigParser()
    try:
        xConfig.read("grammalecte-server-options._global.ini")
        dOpt = xConfig._sections['options']
    except:
        echo("Options file [grammalecte-server-options._global.ini] not found or not readable")
        exit()
    return dOpt


def getConfigOptions (sLang):
    xConfig = configparser.SafeConfigParser()
    try:
        xConfig.read("grammalecte-server-options." + sLang + ".ini")
    except:
        echo("Options file [grammalecte-server-options." + sLang + ".ini] not found or not readable")
        exit()
    try:
        dGCOpt = { k: bool(int(v))  for k, v in xConfig._sections['gc_options'].items() }
    except:
        echo("Error in options file [grammalecte-server-options." + sLang + ".ini]. Dropped.")
        traceback.print_exc()
        exit()
    return dGCOpt


def genUserId ():
    i = 0
    while True:
        yield str(i)
        i += 1


if __name__ == '__main__':

    # initialisation
    oGrammarChecker = grammalecte.GrammarChecker("fr", "Server")
    oSpellChecker = oGrammarChecker.getSpellChecker()
    oLexicographer = oGrammarChecker.getLexicographer()
    oTextFormatter = oGrammarChecker.getTextFormatter()
    gce = oGrammarChecker.getGCEngine()

    echo("Grammalecte v{}".format(gce.version))
    dServerOptions = getServerOptions()
    dGCOptions = getConfigOptions("fr")
    if dGCOptions:
        gce.setOptions(dGCOptions)
    dServerGCOptions = gce.getOptions()
    echo("Grammar options:\n" + " | ".join([ k + ": " + str(v)  for k, v in sorted(dServerGCOptions.items()) ]))
    dUser = {}
    userGenerator = genUserId()

    app = Bottle()

    # GET
    @app.route("/")
    def mainPage ():
        if dServerOptions.get("testpage", False) == "True":
            return HOMEPAGE
            #return template("main", {})
        return SADLIFEOFAMACHINE

    @app.route("/get_options/fr")
    def listOptions ():
        sUserId = request.cookies.user_id
        dOptions = dUser[sUserId]["gc_options"]  if sUserId and sUserId in dUser  else dServerGCOptions
        return '{ "values": ' + json.dumps(dOptions) + ', "labels": ' + json.dumps(gce.getOptionsLabels("fr"), ensure_ascii=False) + ' }'


    # POST
    @app.route("/gc_text/fr", method="POST")
    def gcText ():
        #if len(lang) != 2 or lang != "fr":
        #    abort(404, "No grammar checker available for lang “" + str(lang) + "”")
        bComma = False
        dOptions = None
        sError = ""
        if request.cookies.user_id:
            if request.cookies.user_id in dUser:
                dOptions = dUser[request.cookies.user_id].get("gc_options", None)
                response.set_cookie("user_id", request.cookies.user_id, path="/", max_age=86400) # we renew cookie for 24h
            else:
                response.delete_cookie("user_id", path="/")
        if request.forms.options:
            try:
                dOptions = dict(dServerGCOptions)  if not dOptions  else dict(dOptions)
                dOptions.update(json.loads(request.forms.options))
            except:
                sError = "request options not used"
        sJSON = '{ "program": "grammalecte-fr", "version": "'+gce.version+'", "lang": "'+gce.lang+'", "error": "'+sError+'", "data" : [\n'
        for i, sText in enumerate(txt.getParagraph(request.forms.text), 1):
            if bool(request.forms.tf):
                sText = oTextFormatter.formatText(sText)
            sText = oGrammarChecker.generateParagraphAsJSON(i, sText, dOptions=dOptions, bEmptyIfNoErrors=True, bReturnText=bool(request.forms.tf))
            if sText:
                if bComma:
                    sJSON += ",\n"
                sJSON += sText
                bComma = True
        sJSON += "\n]}\n"
        return sJSON

    @app.route("/set_options/fr", method="POST")
    def setOptions ():
        if request.forms.options:
            sUserId = request.cookies.user_id  if request.cookies.user_id  else next(userGenerator)
            dOptions = dUser[sUserId]["gc_options"]  if sUserId in dUser  else dict(dServerGCOptions)
            try:
                dOptions.update(json.loads(request.forms.options))
                dUser[sUserId] = { "time": int(time.time()), "gc_options": dOptions }
                response.set_cookie("user_id", sUserId, path="/", max_age=86400) # 24h
                return json.dumps(dUser[sUserId]["gc_options"])
            except:
                traceback.print_exc()
                return '{"error": "options not registered"}'
        return '{"error": "no options received"}'

    @app.route("/reset_options/fr", method="POST")
    def resetOptions ():
        if request.cookies.user_id and request.cookies.user_id in dUser:
            del dUser[request.cookies.user_id]
        return "done"

    @app.route("/format_text/fr", method="POST")
    def formatText ():
        return oTextFormatter.formatText(request.forms.text)

    #@app.route('/static/<filepath:path>')
    #def server_static (filepath):
    #    return static_file(filepath, root='./views/static')

    @app.route("/purge_users", method="POST")
    def purgeUsers ():
        "delete user options older than n hours"
        if not request.forms.password or "password" not in dServerOptions or not request.forms.hours:
            return "what?"
        try:
            if request.forms.password == dServerOptions["password"]:
                nNowMinusNHours = int(time.time()) - (int(request.forms.hours) * 60 * 60)
                for nUserId, dValue in dUser.items():
                    if dValue["time"] < nNowMinusNHours:
                        del dUser[nUserId]
                return "done"
            else:
                return "no"
        except:
            traceback.print_exc()
            return "error"

    # ERROR
    @app.error(404)
    def error404 (error):
        return 'Error 404.<br/>' + str(error)

    run(app, \
        host=dServerOptions.get('host', 'localhost'), \
        port=int(dServerOptions.get('port', 8080)))
