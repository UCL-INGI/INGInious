#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Pythia library for writing tasks and feedback scripts (french version)
# Author: Sébastien Combéfis <sebastien@combefis.be>
# Copyright (C) 2012, Université catholique de Louvain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from lib.pythia import *

class FrenchFeedbackMessage(FeedbackMessage):
    
    '''Class for messages generated in the feedbacks: French version'''
    
    def timeexceeded(self):
        return '<p>Votre programme a pris trop de temps pour s\'exécuter en dépassant la limite maximale autorisée.</p>'
    
    def generalerror(self):
        return '<p>Une erreur s\'est produite lors de l\'exécution de votre code.</p>'
    
    def compileerror(self, msg):
        return '<p>Erreur de compilation (votre programme est donc mal écrit) :</p><pre>{}</pre>'.format(clean(msg))
    
    def correct(self):
        return '<p>Votre réponse est correcte.</p>'
    
    def noanswer(self):
        return '<p>Vous n\'avez pas répondu à la question.</p>'
    
    def exception(self, msg):
        return '<p>Votre code a produit une exception (erreur lors de l\'exécution).</p><pre>{}</pre>'.format(clean(msg))
    
    def undeclared(self,var):
        return '<p>Vous n\'avez pas déclaré une variable s\'appelant <b>&#171;&#160;{}&#160;&#187;</b>.</p>'.format(var)
    
    def badtype(self, type):
        return '<p>Votre réponse doit être {}.</p>'.format(type)
    
    def badvalue(self, var, val, paramslist = None, paramsval = None, expected = None):
        header = '<p>Vous n\'avez pas initialisé la variable <b>&#171;&#160;' + var + '&#160;&#187;</b> avec la bonne valeur.'
        if paramslist == None and paramsval == None and expected == None:
            return header + ' Elle contient en effet la valeur ' + val +  '.</p>'
        params = '<b>&#171;&#160;' + paramslist[0] + '&#160;&#187;</b> vaut ' + paramsval[0]
        for i in range(1, len(paramslist)):
            params += (', ' if i < len(paramslist) - 1 else ' et ') + '<b>&#171;&#160;' + paramslist[i] + '&#160;&#187;</b> vaut ' + paramsval[i]
        return header + ' Par exemple, si ' + params + ', vous renvoyez ' + val + ' au lieu de ' + expected + '.</p>'
    
    def unchanged(self, var, val, paramslist = None, paramsval = None, expected = None):
        header = '<p>Vous n\'avez pas mis à jour la variable <b>&#171;&#160;' + var + '&#160;&#187;</b> avec la bonne valeur.'
        if paramslist == None and paramsval == None and expected == None:
            return header + ' Elle contient en effet la valeur ' + val + '.</p>'
        params = '<b>&#171;&#160;' + paramslist[0] + '&#160;&#187;</b> vaut ' + paramsval[0]
       	for i in range(1, len(paramslist)):
            params += (', ' if i < len(paramslist) - 1 else ' et ') + '<b>&#171;&#160;' + paramslist[i] + '&#160;&#187;</b> vaut ' + paramsval[i]
        return header + ' Par exemple, si ' + params + ', sa valeur est ' + val + ' au lieu de ' + expected + '.</p>'
    
    def default(self, code):
        return '<p>Réponse incorrecte ({}).</p>'.format(clean(msg))
