#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import functools
import logging
import uuid

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


def send_task(name, *args):
    """
    Helper for sending a Celery task.

    ``name`` is the name of the task to send. If it doesn't contain a
    ``.`` then it is automatically prefixed with ``ckanext_extractor.``.

    Any remaining arguments are passed to the task.

    A random UUID is generated for the task ID.
    """
    # Late import at call time because it requires a running app
    from ckan.lib.celery_app import celery
    if '.' not in name:
        name = 'ckanext_extractor.' + name
    return celery.send_task(name, args, task_id=str(uuid.uuid4()))

