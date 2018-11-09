#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
#  Copyright (c)  2017 Olivier Martin
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

import subprocess
from inginious import feedback

# Retourne le nombre de lignes dans lesquelles {keyword} apprait du fichiers {fname}
def lcount(keyword, fname):
    with open(fname, 'r') as fin:
        return sum([1 for line in fin if keyword in line])

# Il faut définir une fonction main comme ceci : def main(_):
def main(_):
    if(lcount("?????", "StudentCode/Etudiant.java") > 0):
        feedback.set_global_result('failed')
        feedback.set_global_feedback(_("Il est interdit d'utiliser ?????, même en commentaires."))
        return 1
    return 0

