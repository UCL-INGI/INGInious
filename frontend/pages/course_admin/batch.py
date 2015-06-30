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

from frontend.base import renderer
from frontend.pages.course_admin.utils import get_course_and_check_rights
from frontend.batch_manager import get_all_batch_containers_metadata, add_batch_job, get_all_batch_jobs_for_course

class CourseBatchOperations(object):
    """ Batch operation management """

    def GET(self, courseid):
        """ GET request """

        course, _ = get_course_and_check_rights(courseid, allow_all_staff=False)
        #add_batch_job(course, "ingi/inginious-b-test", {"text": "something"})
        operations = []
        for entry in list(get_all_batch_jobs_for_course(courseid)):
            ne = {"container_name": entry["container_name"],
                  "bid": str(entry["_id"]),
                  "submitted_on": entry["submitted_on"]}
            if "result" in entry:
                ne["status"] = "ok" if entry["result"]["retval"] == 0 else "ko"
            else:
                ne["status"] = "waiting"
            operations.append(ne)

        return renderer.course_admin.batch(course, operations, get_all_batch_containers_metadata())