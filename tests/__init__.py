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
import os
import unittest

import webtest

import app_frontend
import inginious.common.base
import inginious.frontend
import inginious.frontend.session
if not os.path.basename(os.getcwd()) == 'doc':
    app = app_frontend.get_app(os.path.dirname(os.path.realpath(__file__)) + "/configuration.json")
    appt = webtest.TestApp(inginious.common.base.INGIniousConfiguration.get('tests', {}).get('host_url', app.wsgifunc()))
