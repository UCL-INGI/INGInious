# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Auth methods """

from inginious.frontend.webapp.pages.api._api_page import APIPage


class APIAuthMethods(APIPage):
    """
        Endpoint /api/v0/auth_methods
    """

    def API_GET(self):
        """
            Returns all the auth methods available. (200 OK)

            Response: list of auth methods. The value of the dict is an auth method, represented by:

            id
                id of the auth method

            name
                the name of the authentication method, typically displayed by the webapp

            input
                a dictionary containing as key the name of the input (in the HTML sense of name), and, as value,
                a dictionary containing two fields:

                name
                    the placeholder for the input

                type
                    text or password
        """
        to_display = []
        for key, (name, data) in self.user_manager.get_auth_methods().items():
            to_display.append({
                "id": key,
                "name": name,
                "input": [{"id": ik, "name": iv["placeholder"], "type": iv["type"]} for ik, iv in data["input"].items()]
            })

        return 200, to_display
