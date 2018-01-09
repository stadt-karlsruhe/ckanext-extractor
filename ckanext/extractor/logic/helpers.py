#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 Stadt Karlsruhe (www.karlsruhe.de)
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

import functools
import logging

from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def check_access(auth_func_name):
    """
    Decorator for API function authorization.

    Calls the auth function of the given name to make sure that the
    user is authorized to execute the function.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(context, data_dict):
            toolkit.check_access(auth_func_name, context, data_dict)
            return f(context, data_dict)
        return wrapped
    return decorator

