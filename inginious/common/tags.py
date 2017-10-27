# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

class Tag:
    """ This class represents a tag. A tag is a kind of badge that represents a concept. """

    def __init__(self, id, name, visible=True):
        self._id = id
        self._name = name
        self._visible = visible

    def get_name(self):
        """ Returns the name of this tag """
        return _(self._name)

    def get_id(self):
        """ Returns the id of this tag """
        return self._id
        
    def is_visible_for_student(self):
        """ Returns True is the tag should be visible to students """
        return self._visible
        
    @staticmethod
    def get_number_of_visible_tags(list_tags):
        """ Count the number of visible tags for the list_tags. list_tags have to contains only Tag objects """
        count = 0
        for tag in list_tags:
            print(tag.is_visible_for_student())
            if (tag.is_visible_for_student()):
                count =+ 1
        return count
        

    @staticmethod
    def parse_tags_from_string(tag_str):
        """ Parse a string and return a tag dictionnary by ids of tags """
        tag_list = []
        try:
            if isinstance(tag_str, str) and tag_str != "":
                for tag in [x.strip() for x in tag_str.split(',')]: # for exemple : ['id1:nom1', 'id2:nom2', …]
                    [id_tag, nom, visible] = tag.split(':') # can cause ValueError
                    if(visible == "V"):
                        visible = True
                    else:
                        visible = False
                    if(id_tag != "" and nom != ""):
                        tag_list.append(Tag(id_tag, nom, visible))
            return tag_list
        except ValueError:
            raise ValueError(_('the tags field is badly formed !'))
            return []
            