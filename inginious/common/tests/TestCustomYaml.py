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
import tempfile
import shutil
import os
from collections import OrderedDict

import inginious.common.custom_yaml as yaml


class TestCustomLoad(object):
    def setUp(self):
        self.dir_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_load_ordereddict(self):
        open(os.path.join(self.dir_path, "input.yaml"), "w").write("""
        the: a
        order: z
        of: b
        the_: y
        keys: c
        is: x
        important: d
        """)
        loaded = yaml.load(open(os.path.join(self.dir_path, "input.yaml"), "r"))
        assert type(loaded) == OrderedDict
        assert loaded.keys() == ["the", "order", "of", "the_", "keys", "is", "important"]

    def test_load_string(self):
        loaded = yaml.load("""
        the: a
        order: z
        of: b
        the_: y
        keys: c
        is: x
        important: d
        """)
        assert type(loaded) == OrderedDict
        assert loaded.keys() == ["the", "order", "of", "the_", "keys", "is", "important"]


class TestCustomWrite(object):
    def setUp(self):
        self.dir_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_write_ordereddict(self):
        d = OrderedDict([("the", "a"), ("order", "z"), ("is", "b"), ("important", "y")])
        yaml.dump(d, open(os.path.join(self.dir_path, "output.yaml"), "w"))

        loaded = yaml.load(open(os.path.join(self.dir_path, "output.yaml"), "r"))
        assert type(loaded) == OrderedDict
        assert loaded.keys() == ["the", "order", "is", "important"]

    def test_write_string(self):
        d = OrderedDict([("the", "a"), ("order", "z"), ("is", "b"), ("important", "y")])
        string = yaml.dump(d)

        loaded = yaml.load(string)
        assert type(loaded) == OrderedDict
        assert loaded.keys() == ["the", "order", "is", "important"]

    def test_write_long_str(self):
        d = {"key": """This is a very long string
        that should be multiline in the yaml!


        minimum 6 lines!"""}
        string = yaml.dump(d)
        assert len(string.splitlines()) == 6

    def test_write_long_str_obj(self):
        class strange_object(object):
            def __str__(self):
                return """This is a very long string
                    that should be multiline in the yaml!


                    minimum 6 lines!"""

        string = yaml.dump({"key": strange_object()})
        assert len(string.splitlines()) == 6
