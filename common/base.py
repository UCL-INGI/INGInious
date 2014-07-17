import re
import json

class Configuration(dict):
    def load(self,path):
        self.update(json.load(open(path,"r")))
        
INGIniousConfiguration=Configuration()

def IdChecker(idToTest):
    """Checks if a id is correct"""
    return bool(re.match('[a-z0-9\-_]+$', idToTest, re.IGNORECASE))