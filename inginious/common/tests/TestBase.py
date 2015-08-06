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
import os
import tempfile
import shutil
import copy

from inginious.common.base import directory_compare_from_hash, directory_content_with_hash, hash_file, id_checker, load_json_or_yaml, write_json_or_yaml


class TestIdChecker(object):
    """ Test the id checker """

    def test_id_checker_valid_1(self):
        assert id_checker("azertyuiopZERTYUIO65456_5-a") is True

    def test_id_checker_invalid_1(self):
        assert id_checker("a@a") is False

    def test_id_checker_invalid_2(self):
        assert id_checker("") is False

    def test_id_checker_invalid_3(self):
        assert id_checker("test/test") is False


class TestJSONYAMLReaderWriter(object):
    """ Test the functions load_json_or_yaml and write_json_or_yaml """

    def setUp(self):
        self.dir_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_json_read(self):
        open(os.path.join(self.dir_path, "input.json"), "w").write('{"key1":"data1","key2":{"key3":[1,2]}}')
        assert load_json_or_yaml(os.path.join(self.dir_path, "input.json")) == {'key1': 'data1', 'key2': {'key3': [1, 2]}}

    def test_json_write(self):
        write_json_or_yaml(os.path.join(self.dir_path, "output.json"), {'key1': 'data1', 'key2': {'key3': [1, 2]}})
        assert load_json_or_yaml(os.path.join(self.dir_path, "output.json")) == {'key1': 'data1', 'key2': {'key3': [1, 2]}}

    def test_yaml_read(self):
        open(os.path.join(self.dir_path, "input.yaml"), "w").write("""
        key1: data1
        key2:
            key3:
                - 1
                - 2
        """)
        assert load_json_or_yaml(os.path.join(self.dir_path, "input.yaml")) == {'key1': 'data1', 'key2': {'key3': [1, 2]}}

    def test_yaml_write(self):
        write_json_or_yaml(os.path.join(self.dir_path, "output.yaml"), {'key1': 'data1', 'key2': {'key3': [1, 2]}})
        assert load_json_or_yaml(os.path.join(self.dir_path, "output.yaml")) == {'key1': 'data1', 'key2': {'key3': [1, 2]}}


class TestDirectoryHash(object):
    """ Test all the functions that involves file hash """

    def setUp(self):
        self.dir_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_hash_file(self):
        tmp = tempfile.TemporaryFile()
        tmp.write("some random text")
        tmp.flush()
        tmp.seek(0)
        assert hash_file(tmp) == "07671a038c0eb43723d421693b073c3b"

    def test_directory_content_with_hash(self):
        test_dir = os.path.join(self.dir_path, "test1")

        # Create data
        os.mkdir(test_dir)
        os.mkdir(os.path.join(test_dir, "subdir"))

        goal = {}

        open(os.path.join(test_dir, "file1"), "w").write("random text 1")
        goal["file1"] = ("d7e62e68f60f6974309b263192d5fea2", os.stat(os.path.join(test_dir, "file1")).st_mode)

        open(os.path.join(test_dir, "file2"), "w").write("random text 2")
        goal["file2"] = ("5ae848320fda7796dc2f3a1a68300e07", os.stat(os.path.join(test_dir, "file2")).st_mode)

        open(os.path.join(test_dir, "subdir", "file3"), "w").write("random text 3")
        goal["subdir/file3"] = ("312aa75e0816015cdb5ef1989de7bf3f", os.stat(os.path.join(test_dir, "subdir", "file3")).st_mode)

        # Test the function
        assert directory_content_with_hash(test_dir) == goal

    def test_directory_compare_from_hash(self):
        test_dir = os.path.join(self.dir_path, "test2")

        # Create data
        os.mkdir(test_dir)
        os.mkdir(os.path.join(test_dir, "subdir"))
        open(os.path.join(test_dir, "file1"), "w").write("random text 1")
        open(os.path.join(test_dir, "file2"), "w").write("random text 2")
        open(os.path.join(test_dir, "subdir", "file3"), "w").write("random text 3")
        open(os.path.join(test_dir, "file4"), "w").write("random text 4")
        open(os.path.join(test_dir, "file5"), "w").write("random text 5")
        open(os.path.join(test_dir, "file6"), "w").write("random text 6")

        l1 = directory_content_with_hash(test_dir)
        l2 = copy.deepcopy(l1)

        # Pertub the data
        l2["file1"] = (l2["file1"][0], 0)
        l2["file2"] = ("not a valid hash", l2["file2"])
        l2["file4"] = ("not a valid hash", 0)
        del l2["file5"]

        # Compare and test
        to_update, to_delete = directory_compare_from_hash(l2, l1)
        assert set(to_update) == set(["file1", "file2", "file4"])
        assert set(to_delete) == set(["file5"])
