# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Manages users' sessions """
import sys

from common_frontend.plugin_manager import PluginManager
from common_frontend.session import get_session
from webapp.user_data import UserData
import common_frontend.templates
# Add this module to the templates
common_frontend.templates.add_to_template_globals("User", sys.modules[__name__])


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

def get_email():
    """ Returns the email of the current user. Returns None if no user is logged in """
    if not is_logged_in():
        return None
    return get_session().email

def is_logged_in():
    """ Returns if the user is logged in or not """
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
    """ Connect through plugins """
    return PluginManager().get_auth_method_callback(auth_method_id)(login_data)
