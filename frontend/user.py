import ldap
from frontend.session import sessionManager
import common.base

def getUsername():
    """ Returns the username (which is unique) of the current user. Returns None if no user is logged in """
    if not isLoggedIn():
        return None
    return sessionManager.get().username

def getRealname():
    """ Returns the real name of the current user. Returns None if no user is logged in """
    if not isLoggedIn():
        return None
    return sessionManager.get().realname

def isLoggedIn():
    """" Returns if the user is logged in or not """
    return "loggedin" in sessionManager.get() and sessionManager.get().loggedin

def disconnect():
    """ Log off the current user """
    sessionManager.get().loggedin = False
    sessionManager.get().username = None
    sessionManager.get().realname = None
    sessionManager.get().email = None
    return

def connect(self, login, password):
    """Connect throught LDAP"""
    try:
        if not common.base.IdChecker(login):
            return False
        username = "uid=" + login + ",ou=People,dc=info,dc=ucl,dc=ac,dc=be"
        
        # Certificates
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_NEVER)
        
        # Connection to LDAP
        l = ldap.initialize('ldaps://ldap.student.info.ucl.ac.be')
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(username, password)
        
        sessionManager.get().loggedin = True
        
        # Fetch login informations
        results = l.search_s(username, ldap.SCOPE_SUBTREE, '(objectclass=person)', ['mail','cn','uid'])
        
        for req,entry in results:
            sessionManager.get().email = entry['mail'][0]
            sessionManager.get().username = entry['uid'][0]
            sessionManager.get().realname = entry['cn'][0]
        
        return True
    except ldap.LDAPError, e:
        return False