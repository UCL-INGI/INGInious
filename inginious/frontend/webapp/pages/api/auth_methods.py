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
        for key, (name, input) in self.user_manager.get_auth_methods_inputs().iteritems():
            to_display.append({
                "id": key,
                "name": name,
                "input": [{"id": ik, "name": iv["placeholder"], "type": iv["type"]} for ik, iv in input.iteritems()]
            })

        return 200, to_display
