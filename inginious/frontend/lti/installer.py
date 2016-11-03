# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Custom installer for the LTI frontend """
import uuid
import os
import inginious.frontend.common.installer


class Installer(inginious.frontend.common.installer.Installer):
    """ Custom installer for the LTI frontend """

    def configure_download_directory(self):
        """ Configure backup directory """
        self._display_question("Please choose a directory in which to store the download files. Default : lti_download")
        download_directory = None
        while download_directory is None:
            download_directory = self._ask_with_default("Download directory", "lti_download")
            if not os.path.exists(download_directory):
                self._display_error("Path does not exists")
                if self._ask_boolean("Would you like to retry?", True):
                    download_directory = None

        return {"download_directory": download_directory}

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

        self._display_header("DOWNLOAD DIRECTORY")
        self._display_info("LTI module prepares the downloadable archive in a temporary folder before downloading it.")
        download_directory_opt = self.configure_download_directory()
        options.update(download_directory_opt)

        return options

    def configuration_filename(self):
        """ Returns the name of the configuration file """
        return "configuration.lti.yaml"

    def support_remote_debugging(self):
        """ Returns True if the frontend supports remote debugging, False else"""
        return False
