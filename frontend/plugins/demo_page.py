""" A demo plugin that adds a page """


class DemoPage(object):

    """ A simple demo page showing how to add a new page """

    def GET(self):
        """ GET request """
        return "This is a test page :-)"


def init(plugin_manager, _):
    """ Init the plugin """
    plugin_manager.add_page("/test", "frontend.plugins.demo_page.DemoPage")
    print "Started Demo Page"
