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
""" A course class with some modification for users """

from collections import OrderedDict

from inginious.common.courses import Course
from inginious.frontend.common.courses import FrontendCourse
from inginious.frontend.webapp.accessible_time import AccessibleTime


class WebAppCourse(FrontendCourse):
    """ A course with some modification for users """

    def __init__(self, courseid, content, task_factory):
        super(WebAppCourse, self).__init__(courseid, content, task_factory)

        if self._content.get('nofrontend', False):
            raise Exception("That course is not allowed to be displayed directly in the webapp")

        try:
            self._admins = self._content.get('admins', [])
            self._tutors = self._content.get('tutors', [])
            self._accessible = AccessibleTime(self._content.get("accessible", None))
            self._registration = AccessibleTime(self._content.get("registration", None))
            self._registration_password = self._content.get('registration_password', None)
            self._registration_ac = self._content.get('registration_ac', None)
            if self._registration_ac not in [None, "username", "realname", "email"]:
                raise Exception("Course has an invalid value for registration_ac: " + self.get_id())
            self._registration_ac_list = self._content.get('registration_ac_list', [])
            self._groups_student_choice = self._content.get("groups_student_choice", False)
        except:
            raise Exception("Course has an invalid description: " + self.get_id())

    def get_staff(self):
        """ Returns a list containing the usernames of all the staff users """
        return list(set(self.get_tutors() + self.get_admins()))

    def get_admins(self):
        """ Returns a list containing the usernames of the administrators of this course """
        return self._admins

    def get_tutors(self):
        """ Returns a list containing the usernames of the tutors assigned to this course """
        return self._tutors

    def is_open_to_non_staff(self):
        """ Returns true if the course is accessible by users that are not administrator of this course """
        return self._accessible.is_open()

    def is_registration_possible(self, username, realname, email):
        """ Returns true if users can register for this course """
        return self._accessible.is_open() and self._registration.is_open() and self.is_user_accepted_by_access_control(username, realname, email)

    def is_password_needed_for_registration(self):
        """ Returns true if a password is needed for registration """
        return self._registration_password is not None

    def get_registration_password(self):
        """ Returns the password needed for registration (None if there is no password) """
        return self._registration_password

    def get_accessibility(self):
        """ Return the AccessibleTime object associated with the accessibility of this course """
        return self._accessible

    def get_registration_accessibility(self):
        """ Return the AccessibleTime object associated with the registration """
        return self._registration

    def get_tasks(self):
        return OrderedDict(sorted(Course.get_tasks(self).items(), key=lambda t: t[1].get_order()))

    def get_access_control_method(self):
        """ Returns either None, "username", "realname", or "email", depending on the method used to verify that users can register to the course """
        return self._registration_ac

    def get_access_control_list(self):
        """ Returns the list of all users allowed by the AC list """
        return self._registration_ac_list

    def can_students_choose_group(self):
        """ Returns True if the students can choose their groups """
        return self._groups_student_choice

    def is_user_accepted_by_access_control(self, username, realname, email):
        """ Returns True if the user is allowed by the ACL """
        if self.get_access_control_method() is None:
            return True
        elif self.get_access_control_method() == "username":
            return username in self.get_access_control_list()
        elif self.get_access_control_method() == "realname":
            return realname in self.get_access_control_list()
        elif self.get_access_control_method() == "email":
            return email in self.get_access_control_list()
        return False
