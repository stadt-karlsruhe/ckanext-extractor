#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

