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
