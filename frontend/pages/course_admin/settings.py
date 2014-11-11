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
import codecs
import json

import web

from frontend.accessible_time import AccessibleTime
from frontend.base import renderer
from frontend.pages.course_admin.utils import get_course_and_check_rights
import frontend.user as User


class CourseSettings(object):

    """ Couse settings """

    def GET(self, courseid):
        """ GET request """
        course = get_course_and_check_rights(courseid)
        return self.page(course)

    def POST(self, courseid):
        """ POST request """
        course = get_course_and_check_rights(courseid)

        errors = []
        try:
            data = web.input()
            course_content = json.load(open(course.get_course_descriptor_path(courseid), "r"))
            course_content['name'] = data['name']
            if course_content['name'] == "":
                errors.append('Invalid name')
            course_content['admins'] = data['admins'].split(',')
            if User.get_username() not in course_content['admins']:
                errors.append('You cannot remove yourself from the administrators of this course')
            course_content['admins'] = data['admins'].split(',')

            if data["accessible"] == "custom":
                course_content['accessible'] = "{}/{}".format(data["accessible_start"], data["accessible_end"])
            elif data["accessible"] == "true":
                course_content['accessible'] = True
            else:
                course_content['accessible'] = False

            try:
                AccessibleTime(course_content['accessible'])
            except:
                errors.append('Invalid accessibility dates')

            if data["registration"] == "custom":
                course_content['registration'] = "{}/{}".format(data["registration_start"], data["registration_end"])
            elif data["registration"] == "true":
                course_content['registration'] = True
            else:
                course_content['registration'] = False

            try:
                AccessibleTime(course_content['registration'])
            except:
                errors.append('Invalid registration dates')

            course_content['registration_password'] = data['registration_password']
            if course_content['registration_password'] == "":
                course_content['registration_password'] = None
        except:
            errors.append('User returned an invalid form.')

        if len(errors) == 0:
            with codecs.open(course.get_course_descriptor_path(courseid), "w", 'utf-8') as course_file:
                course_file.write(json.dumps(course_content, sort_keys=False, indent=4, separators=(',', ': ')))
            errors = None
            course = get_course_and_check_rights(courseid)  # don't forget to reload the modified course

        return self.page(course, errors, errors is None)

    def page(self, course, errors=None, saved=False):
        """ Get all data and display the page """
        return renderer.admin_course_settings(course, errors, saved)
