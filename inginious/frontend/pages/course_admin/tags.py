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
        tags = OrderedDict(sorted(tags.items(), key=lambda item: item[0]))  # Sort by key

        # Repair tags
        for k in tags:
            tags[k]["visible"] = ("visible" in tags[
                k])  # Since unckecked checkboxes are not present here, we manually add them to avoid later errors
            tags[k]["type"] = int(tags[k]["type"])
            if not "id" in tags[k]:
                tags[k][
                    "id"] = ""  # Since textinput is disabled when the tag is organisational, the id field is missing. We add it to avoid Keys Errors
            if tags[k]["type"] == 2:
                tags[k]["id"] = ""  # Force no id if organisational tag

        # Remove uncompleted tags (tags with no name or no id)
        for k in list(tags.keys()):
            if (tags[k]["id"] == "" and tags[k]["type"] != 2) or tags[k]["name"] == "":
                del tags[k]

        # Find duplicate ids. Return an error if some tags use the same id.
        for k in tags:
            if tags[k]["type"] != 2:  # Ignore organisational tags since they have no id.
                count = 0
                id = str(tags[k]["id"])
                if (" " in id):
                    return json.dumps({"status": "error", "message": _("You can not use spaces in the tag id field.")})
                if not id_checker(id):
                    return json.dumps({"status": "error", "message": _("Invalid tag id: {}").format(id)})
                for k2 in tags:
                    if tags[k2]["type"] != 2 and tags[k2]["id"] == id:
                        count = count + 1
                if count > 1:
                    return json.dumps({"status": "error",
                                       "message": _("Some tags have the same id! The id of a tag must be unique.")})

        return self.show_page(course, web.input())

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return self.show_page(course, web.input())

    def show_page(self, course, user_input):
        return self.template_helper.get_renderer().course_admin.tags(course)
