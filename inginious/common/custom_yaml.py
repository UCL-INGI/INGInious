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
""" A custom YAML based on PyYAML, that provides Ordered Dicts """
# Most ideas for this implementation comes from http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
from collections import OrderedDict

import yaml as original_yaml


def load(stream):
    """
        Parse the first YAML document in a stream
        and produce the corresponding Python
        object. Use OrderedDicts to produce dicts.

        Safe version.
    """

    class OrderedLoader(original_yaml.SafeLoader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        original_yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return original_yaml.load(stream, OrderedLoader)


def dump(data, stream=None, **kwds):
    """
        Serialize a Python object into a YAML stream.
        If stream is None, return the produced string instead.
        Dict keys are produced in the order in which they appear in OrderedDicts.

        Safe version.

        If objects are not "conventional" objects, they will be dumped converted to string with the str() function.
        They will then not be recovered when loading with the load() function.
    """

    # Display OrderedDicts correctly
    class OrderedDumper(original_yaml.SafeDumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            original_yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    # Display long strings correctly
    def _long_str_representer(dumper, data):
        if data.find("\n") != -1:
            # Drop some uneeded data
            # \t are forbidden in YAML
            data = data.replace("\t", "    ")
            # empty spaces at end of line are always useless in INGInious, and forbidden in YAML
            data = "\n".join([p.rstrip() for p in data.split("\n")])
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
        else:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)

    # Default representation for some odd objects
    def _default_representer(dumper, data):
        return _long_str_representer(dumper, str(data))

    OrderedDumper.add_representer(str, _long_str_representer)
    OrderedDumper.add_representer(unicode, _long_str_representer)
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    OrderedDumper.add_representer(None, _default_representer)

    s = original_yaml.dump(data, stream, OrderedDumper, encoding='utf-8', allow_unicode=True, default_flow_style=False, indent=4, **kwds)

    if s is not None:
        return s.decode('utf-8')
    else:
        return
