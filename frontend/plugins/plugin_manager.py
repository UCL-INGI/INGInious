""" Plugin Manager """
import importlib


class PluginManager(object):

    """ Registers an manage plugins """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginManager, cls).__new__(
                cls, *args, **kwargs)
        else:
            raise Exception("You should not instanciate PluginManager more than once")
        return cls._instance

    def __init__(self, app, config):
        self.app = app
        self.plugins = []
        self.hooks = {}
        for entry in config:
            module = importlib.import_module(entry["plugin_module"])
            self.plugins.append(module.init(self, entry))

    @classmethod
    def get_instance(cls):
        """ get the instance of PluginManager """
        return cls._instance

    def add_hook(self, name, callback):
        """ Add a new hook that can be called with the call_hook function """
        hook_list = self.hooks.get(name, [])
        hook_list.append(callback)
        self.hooks[name] = hook_list

    def call_hook(self, name, **kwargs):
        """ Call all hooks registered with this name """
        for func in self.hooks.get(name, []):
            func(**kwargs)

    def add_page(self, pattern, classname):
        """ Add a new page to the web application """
        self.app.add_mapping(pattern, classname)
