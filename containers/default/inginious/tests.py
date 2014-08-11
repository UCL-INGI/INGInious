# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious. If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import json

def load_tests():
    """ Open existing tests file """
    result = {}
    if os.path.exists('/.__tests/__tests.json'):
        f = open('/.__tests/__tests.json', 'r')
        cont = f.read()
        f.close()
    else:
        cont = '{}'
    try:
        result = json.loads(cont)
    except ValueError, e:
        result = {"result":"crash", "text":"Tests file has been modified by user !"}
    return result

def save_tests(rdict):
    """ Save tests file """
    # Check for output folder
    if not os.path.exists('/.__tests'):
        os.makedirs('/.__tests/')
    
    jcont = json.dumps(rdict)
    f = open('/.__tests/__tests.json', 'w')
    f.write(jcont)
    f.close()

# Doing the real stuff
def set_result(tag, value):
    """ Set result value value """
    rdict = load_tests()
    rdict[tag] = value
    save_tests(rdict)

def get_tests_results():
    """ Returns the dictionary containing the feedback """
    rdict = load_tests()
    return rdict
