# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" JobManagerTest plugin """
import inginious.frontend.submission_manager


class JobManagerTest(object):

    """ Returns stats about the job manager for distant tests """

    def GET(self):
        """ GET request """
        return str(inginious.frontend.submission_manager.get_job_manager().get_waiting_jobs_count())


def init(plugin_manager, _):
    """ Init the plugin """
    plugin_manager.add_page("/tests/stats", "inginious.frontend.plugins.job_manager_test.JobManagerTest")
    print "Started JobManagerTest plugin"
