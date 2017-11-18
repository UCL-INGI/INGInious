# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

class Tag:
    """ This class represents a tag. A tag is a kind of badge that represents a concept. """

    def __init__(self, id, name, description="", antitag=False, visible=False, organisational=False):
        self._id = id
        self._name = name
        self._description = description
        self._antitag = antitag
        self._visible = visible
        self._organisational = organisational

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
        
    def is_organisational(self):
        """ Returns True if this tag is for organisational purposes """
        return self._organisational
        
    def is_antitag(self):
        """ Returns True if this tag is an antitag """
        return self._antitag
        
    @staticmethod
    def create_tags_from_dict(tag_dict):
        """ 
            Build a tuple of list of Tag objects based on the tag_dict.
            The tuple contains 3 lists.
            - The first list contains common tags
            - The second list contains antitags
            - The third list contains organisational tags
         """
        tag_list_common = []
        tag_list_antitag = []
        tag_list_organisational = []
        for tag in tag_dict:
            try:
                id = tag_dict[tag]["id"]
                name = tag_dict[tag]["name"]
                visible = tag_dict[tag]["visible"]
                description = tag_dict[tag]["description"]
                organisational = tag_dict[tag]["organisational"]
                antitag = tag_dict[tag]["antitag"]
                
                if(organisational):
                    tag_list_organisational.insert(int(tag), Tag(id, name, description, antitag, visible, organisational))
                elif(antitag):
                    tag_list_antitag.insert(int(tag), Tag(id, name, description, antitag, visible, organisational))
                else:
                    tag_list_common.insert(int(tag), Tag(id, name, description, antitag, visible, organisational))

            except KeyError:
                pass
        return (tag_list_common, tag_list_antitag, tag_list_organisational)
