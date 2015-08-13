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
""" Custom installer for the LTI frontend """
import uuid
import inginious.frontend.common.installer


class Installer(inginious.frontend.common.installer.Installer):
    """ Custom installer for the LTI frontend """

    def frontend_specific_configuration(self, options):
        """ Modify the options for a specific frontend. Should return the new option dict """
        self._display_header("LTI KEYS")
        self._display_info("The LTI frontend uses LTI consumer keys and secret to identify remote Learning Management system. We will now create "
                           "new keys.")
        self._display_info("Example of LTI key:")
        self._display_info("- consumer key: edx")
        self._display_info("- secret: %s" % uuid.uuid4())
        self._display_warning("Do not use the default values!")
        options["lti"] = {}
        while True:
            consumer_key = self._ask_with_default("LTI consumer key", "edx")
            secret = self._ask_with_default("LTI consumer secret", uuid.uuid4())
            options["lti"][consumer_key] = {"secret": secret}
            if not self._ask_boolean("Would you like to add another LTI consumer key?", False):
                break

        self._display_info("Here are the consumer keys you defined:")
        for consumer in options["lti"]:
            self._display_info("- %s / %s" % (consumer, options["lti"][consumer]["secret"]))

        self._display_header("LTI MISC")
        while True:
            try:
                options["nb_submissions_kept"] = int(self._ask_with_default("Maximal number of submission kept per student and per task (0 = "
                                                                            "infinite)", 5))
                if options["nb_submissions_kept"] < 0:
                    raise Exception("Should be a natural")
                break
            except:
                self._display_warning("Invalid integer")

        return options

    def configuration_filename(self):
        """ Returns the name of the configuration file """
        return "configuration.lti.yaml"

    def support_remote_debugging(self):
        """ Returns True if the frontend supports remote debugging, False else"""
        return False