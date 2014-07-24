""" LDAP plugin """

import ldap
import frontend.user


def init(plugin_manager, conf):
    """
        Allow to connect through a LDAP service

        Available configuration:
        ::

            {
                "plugin_module": "frontend.plugins.auth.ldap_auth",
                "url": "ldaps://ldap.test.be",
                "request": "uid={},ou=People",
                "prefix": "",
                "name": "LDAP Login"
            }

        *prefix* is the prefix used internally to distingish user that have the same username on different login services
    """

    def connect(login_data):
        """ Connect throught LDAP """
        try:
            login = login_data["login"]
            password = login_data["password"]

            username = conf.get('request', "uid={},ou=People").format(login)

            # Certificates
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

            # Connection to LDAP
            ldap_instance = ldap.initialize(conf.get('url', "ldaps://ldap.test.be"))
            ldap_instance.protocol_version = ldap.VERSION3
            ldap_instance.simple_bind_s(username, password)

            # Fetch login informations
            results = ldap_instance.search_s(username, ldap.SCOPE_SUBTREE, '(objectclass=person)', ['mail', 'cn', 'uid'])

            if len(results) > 0:
                for _, entry in results:
                    email = entry['mail'][0]
                    username = conf.get('prefix', '') + entry['uid'][0]
                    realname = entry['cn'][0]

                frontend.user.connect_user_internal(username, email, realname)
            return True
        except ldap.LDAPError as _:
            return False

    plugin_manager.register_auth_method(conf.get('name', 'LDAP Login'), {"login": {"type": "text", "placeholder": "Login"}, "password": {"type": "password", "placeholder": "Password"}}, connect)
