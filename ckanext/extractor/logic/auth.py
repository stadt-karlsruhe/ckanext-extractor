#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 Stadt Karlsruhe (www.karlsruhe.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


def _only_sysadmins(context, datadict):
    return {'success': False}


@toolkit.auth_allow_anonymous_access
def _everybody(context, datadict):
    return {'success': True}


extractor_delete = _only_sysadmins
extractor_extract = _only_sysadmins
extractor_list = _everybody
extractor_show = _everybody

