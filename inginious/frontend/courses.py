# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A course class with some modification for users """

import gettext
from collections import OrderedDict

from inginious.common.courses import Course
from inginious.frontend.accessible_time import AccessibleTime
from natsort import natsorted

class WebAppCourse(Course):
    """ A course with some modification for users """

    def __init__(self, courseid, content, course_fs, task_factory, hook_manager):
        super(WebAppCourse, self).__init__(courseid, content, course_fs, task_factory, hook_manager)

        try:
            self._name = self._content['name']
        except:
            raise Exception("Course has an invalid description: " + self.get_id())

        if self._content.get('nofrontend', False):
            raise Exception("That course is not allowed to be displayed directly in the webapp")

        try:
            self._admins = self._content.get('admins', [])
            self._tutors = self._content.get('tutors', [])
            self._accessible = AccessibleTime(self._content.get("accessible", None))
            self._registration = AccessibleTime(self._content.get("registration", None))
            self._registration_password = self._content.get('registration_password', None)
            self._registration_ac = self._content.get('registration_ac', None)
            if self._registration_ac not in [None, "username", "binding", "email"]:
                raise Exception("Course has an invalid value for registration_ac: " + self.get_id())
            self._registration_ac_list = self._content.get('registration_ac_list', [])
            self._groups_student_choice = self._content.get("groups_student_choice", False)
            self._use_classrooms = self._content.get('use_classrooms', True)
            self._allow_unregister = self._content.get('allow_unregister', True)
            self._allow_preview = self._content.get('allow_preview', False)
            self._is_lti = self._content.get('is_lti', False)
            self._lti_keys = self._content.get('lti_keys', {})
            self._lti_send_back_grade = self._content.get('lti_send_back_grade', False)
        except:
            raise Exception("Course has an invalid description: " + self.get_id())

        # Force some parameters if LTI is active
        if self.is_lti():
            self._accessible = AccessibleTime(True)
            self._registration = AccessibleTime(False)
            self._registration_password = None
            self._registration_ac = None
            self._registration_ac_list = []
            self._groups_student_choice = False
            self._use_classrooms = True
            self._allow_unregister = True
            self._allow_preview = False
        else:
            self._lti_keys = {}
            self._lti_send_back_grade = False
            
        # Caches for tag lists
        self._all_tags_cache = None
        self._all_tags_cache_list = {}
        self._all_tags_cache_list_admin = {}
        self._organisational_tags_to_task = {}
        self.update_all_tags_cache()

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
        return self.get_accessibility().is_open()

    def is_registration_possible(self, user_info):
        """ Returns true if users can register for this course """
        return self.get_accessibility().is_open() and self._registration.is_open() and self.is_user_accepted_by_access_control(user_info)

    def is_password_needed_for_registration(self):
        """ Returns true if a password is needed for registration """
        return self._registration_password is not None

    def get_registration_password(self):
        """ Returns the password needed for registration (None if there is no password) """
        return self._registration_password

    def get_accessibility(self, plugin_override=True):
        """ Return the AccessibleTime object associated with the accessibility of this course """
        vals = self._hook_manager.call_hook('course_accessibility', course=self, default=self._accessible)
        return vals[0] if len(vals) and plugin_override else self._accessible

    def get_registration_accessibility(self):
        """ Return the AccessibleTime object associated with the registration """
        return self._registration

    def get_tasks(self):
        return OrderedDict(sorted(list(Course.get_tasks(self).items()), key=lambda t: (t[1].get_order(), t[1].get_id())))

    def get_access_control_method(self):
        """ Returns either None, "username", "binding", or "email", depending on the method used to verify that users can register to the course """
        return self._registration_ac

    def get_access_control_list(self):
        """ Returns the list of all users allowed by the AC list """
        return self._registration_ac_list

    def can_students_choose_group(self):
        """ Returns True if the students can choose their groups """
        return self._groups_student_choice

    def use_classrooms(self):
        """ Returns True if classrooms are used """
        return self._use_classrooms

    def is_lti(self):
        """ True if the current course is in LTI mode """
        return self._is_lti

    def lti_keys(self):
        """ {name: key} for the LTI customers """
        return self._lti_keys if self._is_lti else {}

    def lti_send_back_grade(self):
        """ True if the current course should send back grade to the LTI Tool Consumer """
        return self._is_lti and self._lti_send_back_grade

    def is_user_accepted_by_access_control(self, user_info):
        """ Returns True if the user is allowed by the ACL """
        if self.get_access_control_method() is None:
            return True
        elif not user_info:
            return False
        elif self.get_access_control_method() == "username":
            return user_info["username"] in self.get_access_control_list()
        elif self.get_access_control_method() == "email":
            return user_info["email"] in self.get_access_control_list()
        elif self.get_access_control_method() == "binding":
            return set(user_info["bindings"].keys()).intersection(set(self.get_access_control_list()))
        return False

    def allow_preview(self):
        return self._allow_preview

    def allow_unregister(self, plugin_override=True):
        """ Returns True if students can unregister from course """
        vals = self._hook_manager.call_hook('course_allow_unregister', course=self, default=self._allow_unregister)
        return vals[0] if len(vals) and plugin_override else self._allow_unregister

    def get_name(self, language):
        """ Return the name of this course """
        return self.gettext(language, self._name) if self._name else ""
        
    def get_all_tags(self):
        """ 
        Return a tuple of lists ([common_tags], [anti_tags], [organisational_tags]) all tags of all tasks of this course 
        Since this is an heavy procedure, we use a cache to cache results. Cache should be updated when a task is modified.
        """
        
        if self._all_tags_cache != None:
            return self._all_tags_cache
    
        tag_list_common = set()
        tag_list_misconception = set()
        tag_list_org = set()

        tasks = self.get_tasks()
        for id, task in tasks.items():
            for tag in task.get_tags()[0]:
                tag_list_common.add(tag)
            for tag in task.get_tags()[1]:
                tag_list_misconception.add(tag)
            for tag in task.get_tags()[2]:
                tag_list_org.add(tag)
        
        tag_list_common = natsorted(tag_list_common, key=lambda y: y.get_name().lower())
        tag_list_misconception = natsorted(tag_list_misconception, key=lambda y: y.get_name().lower())
        tag_list_org = natsorted(tag_list_org, key=lambda y: y.get_name().lower())
             
        self._all_tags_cache = (list(tag_list_common), list(tag_list_misconception), list(tag_list_org))
        return self._all_tags_cache
        
    def get_all_tags_names_as_list(self, admin=False, language="en"):
        """ Computes and cache two list containing all tags name sorted by natural order on name """

        if admin:
            if self._all_tags_cache_list_admin != {} and language in self._all_tags_cache_list_admin:
                return self._all_tags_cache_list_admin[language] #Cache hit
        else:
            if self._all_tags_cache_list != {} and language in self._all_tags_cache_list:
                return self._all_tags_cache_list[language] #Cache hit
                        
        #Cache miss, computes everything
        s_stud = set()
        s_admin = set()
        (common, _, org) = self.get_all_tags()
        for tag in common + org:
            # Is tag_name_with_translation correct by doing that like that ?
            tag_name_with_translation = self.gettext(language, tag.get_name()) if tag.get_name() else ""
            s_admin.add(tag_name_with_translation) 
            if tag.is_visible_for_student():
                s_stud.add(tag_name_with_translation) 
        self._all_tags_cache_list_admin[language] = natsorted(s_admin, key=lambda y: y.lower())
        self._all_tags_cache_list[language] = natsorted(s_stud, key=lambda y: y.lower())
        
        if admin:
            return self._all_tags_cache_list_admin[language]
        return self._all_tags_cache_list[language]
        
    def get_organisational_tags_to_task(self):
        """ This build a dict for fast retrive tasks id based on organisational tags. The form of the dict is:
        
            { 'org_tag_1': ['task_id', 'task_id', ...], 
              'org_tag_2' : ['task_id', 'task_id', ...], 
              ... }
         """
        if self._organisational_tags_to_task != {}:
            return self._organisational_tags_to_task

        for taskid, task in self.get_tasks().items():
            for tag in task.get_tags()[2]:
                self._organisational_tags_to_task.setdefault(tag.get_name(), []).append(taskid)

        return self._organisational_tags_to_task
        
    def update_all_tags_cache(self):
        """ Force the cache refreshing """
        
        self._all_tags_cache = None
        self._all_tags_cache_list = {}
        self._all_tags_cache_list_admin = {}
        self._organisational_tags_to_task = {}
            
        self.get_all_tags()
        self.get_all_tags_names_as_list()
        self.get_organisational_tags_to_task()
