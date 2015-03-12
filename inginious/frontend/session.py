# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" Manages the sessions in web.py """
import copy

import web

from inginious.frontend.base import get_database
from inginious.frontend.session_mongodb import MongoStore
def get_session():
    """ Returns the current session """
    return get_session.session


def init(app, session_test=None):
    """ 
        Init the session. Should be call before starting the web.py server
        session_test is specified to emulate a session (used for tests)
    """
    if session_test is None:
        if web.config.get('_session') is None:
            get_session.session = web.session.Session(app, MongoStore(get_database(), 'sessions'))
            web.config._session = get_session.session  # pylint: disable=protected-access
        else:
            get_session.session = web.config._session  # pylint: disable=protected-access
    else:
        get_session.session = AttrDict(copy.deepcopy(session_test))

class AttrDict(dict):
    '''
        Used to fake a ThreadedDict for sessions
    '''
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
