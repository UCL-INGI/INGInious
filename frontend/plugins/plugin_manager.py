""" Plugin Manager """
import importlib
import frontend.base


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
        self.authentication = []

        for entry in config:
            module = importlib.import_module(entry["plugin_module"])
            self.plugins.append(module.init(self, entry))

        frontend.base.add_to_template_globals("PluginManager", self)

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

    def register_auth_method(self, name, input_to_display, callback):
        """
            Register a new authentication method

            name
                the name of the authentication method, typically displayed by the frontend

            input_to_display
                a dictionary containing as key the name of the input (in the HTML sense of name), and, as value,
                a dictionary containing two fields:

                placeholder
                    the placeholder for the input

                type
                    text or password
        """
        self.authentication.append({"name": name, "input": input_to_display, "callback": callback})

    def get_all_authentication_methods(self):
        """
            Return an array of dict containing the following key-value pairs:

            name
                The name of the authentication method

            input
                the inputs to be displayed, as described in the register_auth_method method

            callback
                the callback function

            The key of the dict in the array is the auth_method_id of this method
        """
        return self.authentication

    def get_auth_method_callback(self, auth_method_id):
        """ Returns the callback method of a auth type by it's id """
        return self.authentication[auth_method_id]["callback"]
