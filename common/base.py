""" Basic dependencies for every modules that uses INGInious """
import json
import re


class Configuration(dict):

    """ Config class """

    def load(self, path):
        """ Load the config from a json file """
        self.update(json.load(open(path, "r")))

INGIniousConfiguration = Configuration()


def id_checker(id_to_test):
    """Checks if a id is correct"""
    return bool(re.match(r'[a-z0-9\-_]+$', id_to_test, re.IGNORECASE))
