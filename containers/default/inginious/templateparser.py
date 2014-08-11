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

import re
import json

def parseTemplate(template, data):
    """ Parses a template file
        Replaces all occurences of @@problem_id@@ by the value
        of the 'problem_id' key in data dictionary
    """
    # Check if 'input' in data
    if not 'input' in data:
        raise ValueError("Could not find 'input' in data")
    
    # Parse template
    for field in data['input']:
        regex = re.compile("@([^@]*)@" + field + '@([^@]*)@')
        for prefix, postfix in set(regex.findall(template)):
            rep = "\n".join([prefix + v + postfix for v in data['input'][field].splitlines()])
            template = template.replace("@{0}@{1}@{2}@".format(prefix, field, postfix), rep)
    
    return template
