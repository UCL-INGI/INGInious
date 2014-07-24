""" Manages users' sessions """
import sys

from frontend.plugins.plugin_manager import PluginManager
from frontend.session import session
import frontend.base
import frontend.user_data
# Add this module to the templates
frontend.base.add_to_template_globals("User", sys.modules[__name__])


def get_data():
    """ Get the User Data for the connected user """
    if not is_logged_in():
        return None
    return frontend.user_data.UserData(session.username)


def get_username():
    """ Returns the username (which is unique) of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return session.username


def get_realname():
    """ Returns the real name of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return session.realname


def is_logged_in():
    """" Returns if the user is logged in or not """
    return "loggedin" in session and session.loggedin


def disconnect():
    """ Log off the current user """
    session.loggedin = False
    session.username = None
    session.realname = None
    session.email = None
    return


def connect_user_internal(username, email, realname):
    """ Connect a user. Should only be used by plugins to effectively connect the user. **this function does not make any verifications!** """
    session.loggedin = True
    session.email = email
    session.username = username
    session.realname = realname

    get_data().update_basic_informations(session.realname, session.email)


def connect(auth_method_id, login_data):
    """ Connect throught plugins """
    return PluginManager.get_instance().get_auth_method_callback(auth_method_id)(login_data)
