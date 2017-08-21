# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Custom installer for the web app """

import os
import hashlib

import inginious.frontend.common.installer


class Installer(inginious.frontend.common.installer.Installer):
    """ Custom installer for the WebApp frontend """

    def configure_backup_directory(self):
        """ Configure backup directory """
        self._display_question("Please choose a directory in which to store the backup files. By default, the tool will them in the current "
                               "directory")
        backup_directory = None
        while backup_directory is None:
            backup_directory = self._ask_with_default("Backup directory", ".")
            if not os.path.exists(backup_directory):
                self._display_error("Path does not exists")
                if self._ask_boolean("Would you like to retry?", True):
                    backup_directory = None

        return {"backup_directory": backup_directory}

    def ldap_plugin(self):
        """ Configures the LDAP plugin """
        name = self._ask_with_default("Authentication method name (will be displayed on the login page)", "LDAP")
        prefix = self._ask_with_default("Prefix to append to the username before db storage. Usefull when you have more than one auth method with "
                                        "common usernames.", "")
        ldap_host = self._ask_with_default("LDAP Host", "ldap.your.domain.com")

        encryption = 'none'
        while True:
            encryption = self._ask_with_default("Encryption (either 'ssl', 'tls', or 'none')", 'none')
            if encryption not in ['none', 'ssl', 'tls']:
                self._display_error("Invalid value")
            else:
                break

        base_dn = self._ask_with_default("Base DN", "ou=people,c=com")
        request = self._ask_with_default("Request to find a user. '{}' will be replaced by the username", "uid={}")
        require_cert = self._ask_boolean("Require certificate validation?", encryption is not None)

        return {
            "plugin_module": "inginious.frontend.webapp.plugins.auth.ldap_auth",
            "host": ldap_host,
            "encryption": encryption,
            "base_dn": base_dn,
            "request": request,
            "prefix": prefix,
            "name": name,
            "require_cert": require_cert
        }

    def configure_authentication(self, database):
        """ Configure the authentication """
        options = {"plugins": [], "superadmins": []}

        self._display_info("We will now create the first user.")

        username = self._ask_with_default("Enter the login of the superadmin", "superadmin")
        realname = self._ask_with_default("Enter the name of the superadmin", "INGInious SuperAdmin")
        email = self._ask_with_default("Enter the email address of the superadmin", "superadmin@inginious.org")
        password = self._ask_with_default("Enter the password of the superadmin", "superadmin")

        database.users.insert({"username": username,
                                    "realname": realname,
                                    "email": email,
                                    "password": hashlib.sha512(password.encode("utf-8")).hexdigest(),
                                    "bindings": {}})

        options["superadmins"].append(username)

        while True:
            if not self._ask_boolean("Would you like to add another auth method?", False):
                break

            self._display_info("You can choose an authentication plugin between:")
            self._display_info("- 1. LDAP auth plugin. This plugin allows to connect to a distant LDAP host.")

            plugin = self._ask_with_default("Enter the corresponding number to your choice", '1')
            if plugin not in ['1']:
                continue
            elif plugin == '1':
                options["plugins"].append(self.ldap_plugin())
        return options

    def frontend_specific_configuration(self, options):
        """ Modify the options for a specific frontend. Should return the new option dict """

        database = self.try_mongodb_opts(options["mongo_opt"]["host"], options["mongo_opt"]["database"])

        self._display_header("BACKUP DIRECTORY")
        backup_directory_opt = self.configure_backup_directory()
        options.update(backup_directory_opt)

        self._display_header("AUTHENTIFICATION")
        auth_opts = self.configure_authentication(database)
        options.update(auth_opts)

        self._display_info("You may want to add additional plugins to the configuration file.")

        self._display_header("REMOTE DEBUGGING - IN BROWSER")
        self._display_info("If you want to activate the remote debugging of task in the users' browser, you have to install separately "
                           "INGInious-xterm, which is available on Github, according to the parameters you have given for the hostname and the "
                           "port range given in the configuration of the remote debugging.")
        self._display_info("You can leave the following question empty to disable this feature; remote debugging will still be available, "
                           "but not in the browser.")
        webterm = self._ask_with_default("Please indicate the link to your installation of INGInious-xterm (for example: "
                                  "https://your-hostname.com:8080).","")
        if webterm != "":
            options["webterm"] = webterm
        return options

    def configuration_filename(self):
        """ Returns the name of the configuration file """
        return "configuration.yaml"

    def support_remote_debugging(self):
        """ Returns True if the frontend supports remote debugging, False else"""
        return True
