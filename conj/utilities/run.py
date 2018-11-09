#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
#  Copyright (c)  2016 François Michel, edited by Alexandre Dubray 2017
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import json
import subprocess
import shlex
import sys
import re
from json import JSONDecodeError

from inginious import feedback
from inginious import input

def initTranslations():
    """ Initialise la fonction _() qui permettra de traduire les chaines de caractère. 

        Crée un fichier contenant le code de langue afin que le code Java puisse le récupérer plus tard
    """
    import gettext
    current_locale = input.get_input("@lang")
    with open("student/lang","w+") as f: # This file will be used by Java to get the correct lang
        f.write(current_locale)
    try: # Try to load translations.
        language = gettext.translation ('run', 'student/Translations/translations_run', [current_locale])
        _ = language.gettext
    except OSError:
        _ = gettext.gettext # This will use String id if an error occurs
    return _

_ = initTranslations()

def getfilename(file):
    """ Retourne le nom de fichier (sans l'extension) du fichier nommé file """
    return os.path.splitext(file)[0]

def add_indentation_level(to_indent):
    """ Ajoute l'indentation au message to_indent pour l'insérer dans un code-bloc """
    return '   ' + '   '.join(to_indent.splitlines(keepends=True))

def parsetemplate():
    """ Parse les réponse de l'étudiant

    Cette fonction s'occupe de mettre les réponse de l'étudiant aux endroit appropriés.
    Pour chaque fichier dans le dossiers /task/Templates , si il possède une ou plusieurs
    fois le pattern @@<id-question>@@, la réponse de la question avec l'id <id-question>
    sera placée à la place du pattern et le fichier résultant sera copier dans le dossier
    /task/StudentCode (créer au début de la fonction) avec une extension .java
    """
    os.mkdir('./StudentCode')
    for file in os.listdir('./Templates'):
        filename = getfilename(file)
        input.parse_template('./Templates/' + file,'./StudentCode/' + filename + '.java');

def librairies():
    """Définit l'ensemble des pathfile qui seront utilisé via l'option -cp de javac et java """
    lib = '.'
    lib += ':/usr/share/java/powermock-mockito2-junit-1.7.1/*'
    lib += ':./student'
    lib += ':./src'
    lib += ':./StudentCode'
    return lib

def compile_files(test_file):
    """ Compile l'ensemble des fichier .java nécessaire pour les tests

    Compile l'ensemble des fichiers de test. Seul la compilation de ces fichier
    doit être faite car le compilateur de java compilera les classes dont ils
    ont besoin pour fonctionner

    Keyword arguments:
    test_file -- La liste des fichier de tests
    """
    Log = ""
    javac_cmd = "javac -d ./student -encoding UTF8 -cp " + librairies()
    with open('LogCompile.log','w+') as f:
        subprocess.call(shlex.split(javac_cmd) + test_file, universal_newlines=True,stderr=f)
        if os.path.getsize('LogCompile.log') > 0:
            f.seek(0)
            Log = f.read()
    return Log

def get_test_files(runner):
    """Retourne la liste de l'ensemble des nom fichiers de test trouvé dans /task/src

    Cette méthode est appelée uniquement si aucune liste n'est fournie dans le fichier
    config.json. Si c'est le cas, un fichier de test est un fichier tel que
        - Il se trouve dans le dossiers src
        - Il est différent du fichier runner
        - Il n'est pas le fichier de correction (qui s'appelle d'office Correction.java)
        - C'est un fichier .java

    La liste retournée contient uniquement les noms récupérer via getfilename

    Keyword arguments:
    runner -- le nom du fichier runner
    """
    files = []
    for file in os.listdir('./src'):
        if getfilename(file) != runner and not file.startswith('Correction') and not os.path.isdir("./src/"+file) and file.endswith('.java'):
            files.append(getfilename(file))
    return files

def run(customscript,execcustom,nexercices,tests=[],runner='Runner'):
    """ Parse les réponse des étudiant, compile et lance les tests et donne le feedback aux étudiant

    Keyword arguments:
    customscript -- nom d'un script personnalisé
    execcustom -- Si oui (valeur != 0) ou non (0) il faut exécuter le script personnalisé customscript
    nexercices -- la nombre d'exercice dans la tâche
    tests -- Fichiers de test à lancer
    runner -- Fichier runner (default 'Runner')
    """
    #Récupération des fichiers de tests si jamais il ne sont pas fournis à l'appel de la méthode
    if not tests:
        tests = get_test_files(runner)
        code_litteral = ".. code-block::\n\n" 
    parsetemplate() # Parse les réponses de l'étudiant
    if execcustom != 0: # On doit exécuter le script personnalsé
        # If this is a python script we call the main() method with the _() function to transmit the translation mechanism
        if (customscript == "custom_translatable.py"):
            from custom_translatable import main
            outcustom = main(_)
        else:
            outcustom = subprocess.call(['./' + customscript],universal_newlines=True)
        if outcustom != 0: # Le script a renvoyé une erreur
            exit()

    # On compile les fichier. La fonction map applique une fonction (argument 1) sur une liste (argument 2)
    # L'expression lambda définit une fonction anonyme qui ajoute le dossiers src et l'extension .java aux nom de fichier tests
    anonymous_fun = lambda file : './src/' + file + '.java' # Create anonymous funcntion
    Log = compile_files([anonymous_fun(file) for file in tests+[runner]] )
    if Log == "": # La compilation a réussie
        with open('err.txt', 'w+', encoding="utf-8") as f:
            # On lance le runner
            os.chdir('./student')
            java_cmd = "run_student java -ea -cp " + librairies()
            # On passe comme argument au fichier runner les fichier de tests (Voir documentation runner)
            resproc = subprocess.Popen( shlex.split(java_cmd) + ['src/' + runner] + tests, universal_newlines=True, stderr=f, stdout=subprocess.PIPE)
            resproc.communicate()
            resultat = resproc.returncode
            f.flush()
            f.seek(0)
            outerr = f.read()
            print(outerr) # On affiche la sortie de stderr dans les informations de debug
            if resultat == 127: # Les tests ont réussis
                feedback.set_global_result('success')
            elif resultat == 252: # Limite de mémoire dépassée
                feedback.set_global_result('failed')
                feedback.set_global_feedback(_("La limite de mémoire de votre programme est dépassée"))
            elif resultat == 253: # timeout
                feedback.set_global_result('failed')
                feedback.set_global_feedback(_("La limite de temps d'exécution de votre programme est dépassée"))
            else: # Les tests ont échouées
                if nexercices == 1:
                    outerr = add_indentation_level(outerr) # On ajoute de l'indentation pour que ça s'affiche dans un cadre gris pour les étudiants
                    feedback.set_global_result('failed')
                    feedback.set_global_feedback(_("Il semble que vous ayiez fait des erreurs dans votre code…\n\n") + code_litteral + outerr + "\n")
                else:
                    i = 1
                    while i <= nexercices:
                        """
                        Cette regex va matcher tout ce qui se trouve entre
                            - @i (avec i le numéro du sous-problème que l'on considère
                            - @<un ou plusieurs chiffre>

                        et donc matcher tout les feedback associés au sous-problème que l'on considère
                        """
                        regex = '@' + str(i) + ' :\n(.*?)(?=@\d+ :|$)'
                        regex_question = re.findall(regex, outerr, re.DOTALL)
                        if len(regex_question) == 0: # Il n'y a pas de match pour la regex, le sous-problème est bien répondu
                            feedback.set_problem_feedback(_("Vous avez bien répondu à cette question"), "q" + str(i))
                        else:
                            outerr_question = ''.join(regex_question) # On remet tout les feedback trouvé en un seul
                            outerr_question = add_indentation_level(outerr_question) # on l'indente
                            feed = _("Il semble que vous ayiez fait des erreurs dans votre code…\n\n") + code_litteral + outerr_question + "\n"
                            feedback.set_problem_feedback(feed,"q"+str(i))
                        i += 1
    else: # La compilation a raté
        Log = add_indentation_level(Log)
        feed = _("Le programme ne compile pas : \n") + code_litteral + Log + "\n"
        feedback.set_global_result('failed')
        feedback.set_global_feedback(feed)

if __name__ == '__main__':
    try:
        task_options = json.load(open('config.json', 'r', encoding="utf-8"))
    except JSONDecodeError as e:
        print(_("Impossible de décoder le config.json"))
        print(e)
        exit()
    run(**task_options)
