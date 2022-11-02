# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pytest

from inginious.common.additional_field import AdditionalField


@pytest.fixture()
def init():
    af = AdditionalField("test", "a description", 1)
    yield af


class TestAdditionalField(object):
    """Test for additional field class"""

    def test_additional_field_init(self, init):
        af = init
        assert af is not None
        af = AdditionalField(0, "a description", 1)
        try:
            af = AdditionalField("fail", "a description", 99)
        except Exception:
            assert True

    def test_additional_field_get_id(self, init):
        af = init
        assert af.get_id() == "test"

    def test_additional_field_get_description(self, init):
        af = init
        assert af.get_description() == "a description"

    def test_additional_field_get_type_name(self, init):
        af = init
        assert af.get_type_name() == "INTEGER"

    def test_additional_field_get_type(self, init):
        af = init
        assert af.get_type() == 1
