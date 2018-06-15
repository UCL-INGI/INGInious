# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

class Tag:
    """ 
    This class represents a tag. A tag is a kind of badge that represents a concept. 
    The 'type' represents the behaviour of the tag:
    - 0: Skill tags. It appear in blue. When the tag is activated it becomes green. We can perform tasks search on this tag.
    - 1: Misconception tags. It does not appear until it is activated. It appear in red when activated. We can NOT perform tasks search on this tag.
                        The tags are useful to highlight errors or misconceptions.
    - 2: Category tags. Never appear. Only used for organisation and when we perform tasks search.
    """

    def __init__(self, id, name, description="", visible=False, type=0):
        self._id = id
        self._name = name
        self._description = description
        self._visible = visible
        self._type = type
        
    def __eq__(self, other):
        return self._id == other._id and self._name == other._name
        
    def __hash__(self):
        return hash((self._id, self._name))

    def get_name(self):
        """ Returns the name of this tag """
        return self._name

    def get_id(self):
        """ Returns the id of this tag """
        return self._id

    def is_visible_for_student(self):
        """ Returns True is the tag should be visible to students """
        return self._visible

    def get_description(self, translated=False):
        """ 
        Returns the description of this tag 
        translated=True can be use to avoid getting garbage when calling _() with an empty string since the description of a tag CAN be empty
        """
        if translated and self._description != "":
            return _(self._description)
        return self._description
        
    def is_organisational(self):
        """ Returns True if this tag is for organisational purposes """
        return self._type == 2
        
    def is_misconception(self):
        """ Returns True if this tag is an misconception """
        return self._type == 1
        
    def get_type_as_str(self):
        """ Return a textual description of the type """
        if self.get_type() == 0:
            return _("Skill")
        elif self.get_type() == 1:
            return _("Misconception")
        elif self.get_type() == 2:
            return _("Category")
        else:
            return _("Unknown type")
            
    def get_type(self):
        return self._type
        
    @staticmethod
    def create_tags_from_dict(tag_dict):
        """ 
            Build a tuple of list of Tag objects based on the tag_dict.
            The tuple contains 3 lists.
            - The first list contains skill tags
            - The second list contains misconception tags
            - The third list contains category tags
         """
        tag_list_common = []
        tag_list_misconception = []
        tag_list_organisational = []
        for tag in tag_dict:
            try:
                id = tag_dict[tag]["id"]
                name = tag_dict[tag]["name"]
                visible = tag_dict[tag]["visible"]
                description = tag_dict[tag]["description"]
                type = tag_dict[tag]["type"]
                
                if(type == 2):
                    tag_list_organisational.insert(int(tag), Tag(id, name, description, visible, 2))
                elif(type == 1):
                    tag_list_misconception.insert(int(tag), Tag(id, name, description, visible, 1))
                else:
                    tag_list_common.insert(int(tag), Tag(id, name, description, visible, 0))

            except KeyError:
                pass
        return tag_list_common, tag_list_misconception, tag_list_organisational
