""" Manages users' sessions """
import sys

from frontend.plugins.plugin_manager import PluginManager
from frontend.session import get_session
from frontend.user_data import UserData
import frontend.base
# Add this module to the templates
frontend.base.add_to_template_globals("User", sys.modules[__name__])


def get_data():
    """ Get the User Data for the connected user """
    if not is_logged_in():
        return None
    return UserData(get_session().username)


def get_username():
    """ Returns the username (which is unique) of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return get_session().username


def get_realname():
    """ Returns the real name of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return get_session().realname


def is_logged_in():
    """" Returns if the user is logged in or not """
    return "loggedin" in get_session() and get_session().loggedin


def disconnect():
    """ Log off the current user """
    get_session().loggedin = False
    get_session().username = None
    get_session().realname = None
    get_session().email = None
    return


def connect_user_internal(username, email, realname):
    """ Connect a user. Should only be used by plugins to effectively connect the user. **this function does not make any verifications!** """
    get_session().loggedin = True
    get_session().email = email
    get_session().username = username
    get_session().realname = realname

    get_data().update_basic_informations(get_session().realname, get_session().email)


def connect(auth_method_id, login_data):
    """ Connect throught plugins """
    return PluginManager.get_instance().get_auth_method_callback(auth_method_id)(login_data)
