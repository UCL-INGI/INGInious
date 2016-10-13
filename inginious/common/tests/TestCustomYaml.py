# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

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
        with open(os.path.join(self.dir_path, "input.yaml"), "w") as f:
            f.write("""
            the: a
            order: z
            of: b
            the_: y
            keys: c
            is: x
            important: d
            """)
        with open(os.path.join(self.dir_path, "input.yaml"), "r") as f:
            loaded = yaml.load(f)
        assert type(loaded) == OrderedDict
        assert list(loaded.keys()) == ["the", "order", "of", "the_", "keys", "is", "important"]

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
        assert list(loaded.keys()) == ["the", "order", "of", "the_", "keys", "is", "important"]


class TestCustomWrite(object):
    def setUp(self):
        self.dir_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_write_ordereddict(self):
        d = OrderedDict([("the", "a"), ("order", "z"), ("is", "b"), ("important", "y")])
        with open(os.path.join(self.dir_path, "output.yaml"), "w") as f:
            yaml.dump(d, f)

        with open(os.path.join(self.dir_path, "output.yaml"), "r") as f:
            loaded = yaml.load(f)
        assert type(loaded) == OrderedDict
        assert list(loaded.keys()) == ["the", "order", "is", "important"]

    def test_write_string(self):
        d = OrderedDict([("the", "a"), ("order", "z"), ("is", "b"), ("important", "y")])
        string = yaml.dump(d)

        loaded = yaml.load(string)
        assert type(loaded) == OrderedDict
        assert list(loaded.keys()) == ["the", "order", "is", "important"]

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
