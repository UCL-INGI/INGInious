# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pytest

from inginious.common.course_user_setting import CourseUserSetting


@pytest.fixture()
def init():
    af = CourseUserSetting("test", "a description", 1)
    yield af


class TestCourseUserSetting(object):
    """Test for course user settings class"""

    def test_course_user_settings_init(self, init):
        af = init
        assert af is not None
        af = CourseUserSetting(0, "a description", 1)
        try:
            af = CourseUserSetting("fail", "a description", 99)
        except Exception:
            assert True

    def test_course_user_settings_get_id(self, init):
        af = init
        assert af.get_id() == "test"

    def test_course_user_settings_get_description(self, init):
        af = init
        assert af.get_description() == "a description"

    def test_course_user_settings_get_type_name(self, init):
        af = init
        assert af.get_type_name() == "INTEGER"

    def test_course_user_settings_get_type(self, init):
        af = init
        assert af.get_type() == 1
