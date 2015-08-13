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
""" Custom installer for the web app """
import inginious.frontend.common.installer


class Installer(inginious.frontend.common.installer.Installer):
    """ Custom installer for the LTI frontend """

    def configure_batch_containers(self, current_options):
        """ Configures the container dict """
        containers = [
            ("ingi/inginious-b-jplag", "Plagiarism detection")
        ]

        default_download = []

        self._display_question("The web app supports a feature called 'batch containers' that allows to apply batch operations on all submissions "
                               "of a course.")
        self._display_question("Please note that the download of these images can take a lot of time, so choose only the images you need")

        options = {"batch_containers": []}
        to_download = []
        for container_name, description in containers:
            if self._ask_boolean("Download %s (%s) ?" % (container_name, description), container_name in default_download):
                to_download.append(container_name)
                options["batch_containers"].append(container_name)

        self.download_containers(to_download, current_options)

        wants = self._ask_boolean("To you want to manually add some images?", False)
        while wants:
            image = self._ask_with_default("Container image name (leave this field empty to skip)", "")
            if image == "":
                break
            options["batch_containers"].append(image)

        self._display_info("Configuration of the batch containers done.")
        return options

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

    def test_auth_plugin(self):
        """  Configures the demo auth plugin """
        name = self._ask_with_default("Authentication method name (will be displayed on the login page)", "Demo")
        users = {}

        self._display_question("Let's add some users")
        while True:
            name = self._ask_with_default("Username", "test")
            password = self._ask_with_default("Password", "test")
            users[name] = password
            if not self._ask_boolean("Would you like to add another user?", False):
                break

        return {
            "plugin_module": "inginious.frontend.webapp.plugins.auth.demo_auth",
            "name": name,
            "users": users
        }

    def db_auth_plugin(self):
        """  Configures the db auth plugin """
        name = self._ask_with_default("Authentication method name (will be displayed on the login page)", "WebApp")

        return {
            "plugin_module": "inginious.frontend.webapp.plugins.auth.db_auth",
            "name": name
        }

    def configure_authentication(self):
        """ Configure the authentication plugins """
        options = {"plugins": []}
        while True:
            self._display_info("You can choose an authentication plugin between:")
            self._display_info("- 1. Test auth plugin. This plugin allows you to test locally INGInious, "
                               "using password defined in the config file.")
            self._display_info("- 2. DB auth plugin. This plugin stores users on the web app database and supports"
                               "self registration")
            self._display_info("- 3. LDAP auth plugin. This plugin allows to connect to a distant LDAP host.")

            plugin = self._ask_with_default("Enter the corresponding number to your choice", '1')
            if plugin not in ['1', '2', '3']:
                continue
            elif plugin == '1':
                options["plugins"].append(self.test_auth_plugin())
            elif plugin == '2':
                already_in = False
                for p in options["plugins"]:
                    if p["plugin_module"] == "inginious.frontend.webapp.plugins.auth.db_auth":
                        already_in = True

                if not already_in:
                    options["plugins"].append(self.db_auth_plugin())
                else:
                    self._display_warning("DB auth plugin cannot be set more than once !")
            elif plugin == '3':
                options["plugins"].append(self.ldap_plugin())

            if not self._ask_boolean("Would you like to add another auth method?", False):
                break
        return options

    def frontend_specific_configuration(self, options):
        """ Modify the options for a specific frontend. Should return the new option dict """
        self._display_header("BATCH CONTAINERS")
        batch_opts = self.configure_batch_containers(options)
        options.update(batch_opts)

        self._display_header("AUTHENTIFICATION")
        auth_opts = self.configure_authentication()
        options.update(auth_opts)

        self._display_info("You may want to add additionnal plugins to the configuration file.")

        self._display_info("We will now add superadmin users.")
        options["superadmins"] = []
        while True:
            superadmin = self._ask_with_default("Enter the login of a superadmin (leave empty to skip this step)", "")
            if superadmin == "":
                break
            options["superadmins"].append(superadmin)

        return options

    def configuration_filename(self):
        """ Returns the name of the configuration file """
        return "configuration.yaml"

    def support_remote_debugging(self):
        """ Returns True if the frontend supports remote debugging, False else"""
        return True