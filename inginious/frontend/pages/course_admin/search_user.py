# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import json
import re

from flask import Response
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseAdminSearchUserPage(INGIniousAdminPage):
    """ Return users based on their username or realname """

    def GET_AUTH(self, courseid, request):  # pylint: disable=arguments-differ
        """ GET request """
        # check rights
        self.get_course_and_check_rights(courseid, allow_all_staff=True)

        request = re.escape(request) # escape for safety. Maybe this is not needed...
        users = list(self.database.users.find({"$or": [{"username": {"$regex": ".*" + request + ".*", "$options": "i"}},
                                                       {"realname": {"$regex": ".*" + request + ".*", "$options": "i"}}
                                                      ]}, {"username": 1, "realname": 1}).limit(10))
        return Response(content_type='text/json; charset=utf-8',response=json.dumps([[
            {'username': entry['username'], 'realname': entry['realname']}
            for entry in users
        ]]))
