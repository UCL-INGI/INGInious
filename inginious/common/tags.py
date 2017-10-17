# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

class Tag:
	""" This class represents a tag. A tag is a kind of badge that represents a concept. """
    
	def __init__(self, id, name):
		self._id = id
		self._name = name

	def get_name(self):
		""" Returns the name of this tag """
		return self._name

	def get_id(self):
		""" Returns the id of this tag """
		return self._id
	
	@staticmethod
	def parse_tag_str(tag_str):
		""" Parse a string and return a tag dictionnary by ids of tags """
		tag_list = []
		try:
			if isinstance(tag_str, str) and tag_str != "":
				for tag in [x.strip() for x in tag_str.split(',')]: # for exemple : ['id1:nom1', 'id2:nom2', …]
					[id_tag, nom] = tag.split(':') # can cause ValueError
					if(id_tag != "" and nom != ""):
						tag_list.append(Tag(id_tag, nom))
			return tag_list 
		except ValueError:
			raise ValueError(_('the tags field is badly formed !'))
			return []		