""" Manages users' sessions """
import sys

import ldap

import common.base
import frontend.base
from frontend.session import session
# Add this module to the templates
frontend.base.add_to_template_globals("User", sys.modules[__name__])


def get_data():
    """ Get the User Data for the connected user """
    if not is_logged_in():
        return None
    import frontend.user_data
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


def connect(login, password):
    """Connect throught LDAP"""
    try:
        if not common.base.id_checker(login):
            return False
        username = "uid=" + login + ",ou=People,dc=info,dc=ucl,dc=ac,dc=be"

        # Certificates
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        # Connection to LDAP
        ldap_instance = ldap.initialize('ldaps://ldap.student.info.ucl.ac.be')
        ldap_instance.protocol_version = ldap.VERSION3
        ldap_instance.simple_bind_s(username, password)

        session.loggedin = True

        # Fetch login informations
        results = ldap_instance.search_s(username, ldap.SCOPE_SUBTREE, '(objectclass=person)', ['mail', 'cn', 'uid'])

        for _, entry in results:
            session.email = entry['mail'][0]
            session.username = entry['uid'][0]
            session.realname = entry['cn'][0]

        # Save everything in the database
        get_data().update_basic_informations(session.realname, session.email)
        return True
    except ldap.LDAPError as _:
        return False
