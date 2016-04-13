#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import uuid


def send_task(name, *args):
    """
    Helper for sending a Celery task.

    ``name`` is the name of the task to send. If the name doesn't
    contain a ``.`` then it is prefixed with ``extractor.``.

    Any remaining arguments are passed to the task.

    A random UUID is generated for the task ID.
    """
    # Late import at call time because it requires a running app
    from ckan.lib.celery_app import celery
    if '.' not in name:
        name = 'extractor.' + name
    return celery.send_task(name, args, task_id=str(uuid.uuid4()))

