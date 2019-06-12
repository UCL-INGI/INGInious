# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import json
import re
import web
from bson.objectid import ObjectId
from collections import OrderedDict
from inginious.common.base import id_checker
from inginious.frontend.pages.course_admin.utils import INGIniousSubmissionAdminPage


class CourseTagsPage(INGIniousSubmissionAdminPage):
    """ Replay operation management """

    @classmethod
    def dict_from_prefix(cls, prefix, dictionary):
        """
            >>> from collections import OrderedDict
            >>> od = OrderedDict()
            >>> od["problem[q0][a]"]=1
            >>> od["problem[q0][b][c]"]=2
            >>> od["problem[q1][first]"]=1
            >>> od["problem[q1][second]"]=2
            >>> AdminCourseEditTask.dict_from_prefix("problem",od)
            OrderedDict([('q0', OrderedDict([('a', 1), ('b', OrderedDict([('c', 2)]))])), ('q1', OrderedDict([('first', 1), ('second', 2)]))])
        """
        o_dictionary = OrderedDict()
        for key, val in dictionary.items():
            if key.startswith(prefix):
                o_dictionary[key[len(prefix):].strip()] = val
        dictionary = o_dictionary

        if len(dictionary) == 0:
            return None
        elif len(dictionary) == 1 and "" in dictionary:
            return dictionary[""]
        else:
            return_dict = OrderedDict()
            for key, val in dictionary.items():
                ret = re.search(r"^\[([^\]]+)\](.*)$", key)
                if ret is None:
                    continue
                return_dict[ret.group(1)] = cls.dict_from_prefix("[{}]".format(ret.group(1)), dictionary)
            return return_dict

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        # Tags
        tags = self.dict_from_prefix("tags", web.input())
        if tags is None:
            tags = {}

        tags_id = [tag["id"] for key, tag in tags.items() if tag["id"]]

        if len(tags_id) != len(set(tags_id)):
            return self.show_page(course, False, _("Some tags have the same id! The id of a tag must be unique."))

        tags = {tag["id"]: tag for key, tag in tags.items() if tag["id"]}

        # Repair tags
        for key, tag in tags.items():
            # Since unckecked checkboxes are not present here, we manually add them to avoid later errors
            tag["visible"] = "visible" in tag
            tag["type"] = int(tag["type"])

            if (tag["id"] == "" and tag["type"] != 2) or tag["name"] == "":
                return self.show_page(course, False, _("Some tag fields were missing."))

            if not id_checker(tag["id"]):
                return self.show_page(course, False,  _("Invalid tag id: {}").format(tag["id"]))

            del tag["id"]

        course_content = self.course_factory.get_course_descriptor_content(courseid)
        course_content["tags"] = tags
        self.course_factory.update_course_descriptor_content(courseid, course_content)

        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        return self.show_page(course, True, "")

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return self.show_page(course, False, "")

    def show_page(self, course, saved, error):
        return self.template_helper.get_renderer().course_admin.tags(course, saved, error)
