import re
import json

#Import configuration
INGIniousConfiguration=json.load(open("./configuration.json","r"))

def IdChecker(idToTest):
    """Checks if a id is correct"""
    return bool(re.match('[a-z0-9\-_]+$', idToTest, re.IGNORECASE))