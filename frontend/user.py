""" Manages users' sessions """
import sys

from frontend.plugins.plugin_manager import PluginManager
import frontend.session
import frontend.base
import frontend.user_data
# Add this module to the templates
frontend.base.add_to_template_globals("User", sys.modules[__name__])


def get_data():
    """ Get the User Data for the connected user """
    if not is_logged_in():
        return None
    return frontend.user_data.UserData(frontend.session.session.username)


def get_username():
    """ Returns the username (which is unique) of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return frontend.session.session.username


def get_realname():
    """ Returns the real name of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return frontend.session.session.realname


def is_logged_in():
    """" Returns if the user is logged in or not """
    return "loggedin" in frontend.session.session and frontend.session.session.loggedin


def disconnect():
    """ Log off the current user """
    frontend.session.session.loggedin = False
    frontend.session.session.username = None
    frontend.session.session.realname = None
    frontend.session.session.email = None
    return


def connect_user_internal(username, email, realname):
    """ Connect a user. Should only be used by plugins to effectively connect the user. **this function does not make any verifications!** """
    frontend.session.session.loggedin = True
    frontend.session.session.email = email
    frontend.session.session.username = username
    frontend.session.session.realname = realname

    get_data().update_basic_informations(frontend.session.session.realname, frontend.session.session.email)


def connect(auth_method_id, login_data):
    """ Connect throught plugins """
    return PluginManager.get_instance().get_auth_method_callback(auth_method_id)(login_data)
