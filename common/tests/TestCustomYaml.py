import tempfile
import shutil
import os
from collections import OrderedDict

import common.custom_yaml as yaml


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
