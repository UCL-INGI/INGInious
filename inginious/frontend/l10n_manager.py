# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import gettext
from flask import session as flask_session

class L10nManager:

    def __init__(self):
        self.translations = {}
        self._session = flask_session

    def get_translation_obj(self, lang=None):
        if lang is None:
            lang = self._session.get("language", "")
        return self.translations.get(lang, gettext.NullTranslations())

    def gettext(self, *args, **kwargs):
        return self.get_translation_obj().gettext(*args, **kwargs)