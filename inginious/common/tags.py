# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

class Tag:
    """ This class represents a tag. A tag is a kind of badge that represents a concept. """

    def __init__(self, id, name, visible=True, description=""):
        self._id = id
        self._name = name
        self._visible = visible
        self._description = description

    def get_name(self):
        """ Returns the name of this tag """
        return _(self._name)

    def get_id(self):
        """ Returns the id of this tag """
        return self._id

    def is_visible_for_student(self):
        """ Returns True is the tag should be visible to students """
        return self._visible

    def get_description(self):
        """ Returns the description of this tag """
        if self._description == "":
            return "" # Without this, _("") return strange things
        return _(self._description)

    @staticmethod
    def create_tags_from_dict(tag_dict):
        """ Build a list of Tag objects based on the tag_dict """
        tag_list = []
        for tag in tag_dict:
            try:
                id = tag_dict[tag]["id"]
                name = tag_dict[tag]["name"]
                visible = tag_dict[tag]["visible"]
                description = tag_dict[tag]["description"]
                tag_list.insert(int(tag), Tag(id, name, visible, description))
            except KeyError:
                pass
        return tag_list
