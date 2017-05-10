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

import contextlib
import datetime
import os.path
import re
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer
from threading import Thread
import time

from celery import current_app
import mock
from nose.tools import assert_raises, assert_true, assert_false

from ckan.logic import NotAuthorized, ValidationError
from ckan.tests.helpers import call_action

from ..model import ResourceMetadata, ResourceMetadatum


def assert_equal(actual, expected, msg=''):
    """
    Assert that two values are equal.

    Like ``nose.tools.assert_equal`` but upon mismatch also displays the
    expected and actual values even if a message is given.
    """
    if actual == expected:
        return
    diff_msg = 'Got {!r} but expected {!r}.'.format(actual, expected)
    raise AssertionError((msg + ' ' + diff_msg).strip())


def fake_process(res_dict):
    """
    Mark resource metadata as processed by removing its task ID.
    """
    metadata = get_metadata(res_dict)
    metadata.task_id = None
    metadata.last_url = res_dict['url']
    metadata.last_format = res_dict['format']
    metadata.save()


def assert_no_metadata(res_dict):
    """
    Assert that no metadata are stored for a resource.
    """
    if ResourceMetadata.filter_by(resource_id=res_dict['id']).count() > 0:
        raise AssertionError(('Found unexcepted metadata for resource '
                             + '"{id}".').format(id=res_dict['id']))
    if ResourceMetadatum.filter_by(resource_id=res_dict['id']).count() > 0:
        raise AssertionError(('Found unexcepted metadatum for resource '
                             + '"{id}".').format(id=res_dict['id']))


def get_metadata(res_dict):
    """
    Shortcut to get metadata for a resource.
    """
    return ResourceMetadata.one(resource_id=res_dict['id'])


def call_action_with_auth(action, context=None, **kwargs):
    """
    Call an action with authorization checks.

    Like ``ckan.tests.helpers.call_action``, but authorization are
    not bypassed.
    """
    if context is None:
        context = {}
    context['ignore_auth'] = False
    return call_action(action, context, **kwargs)


def assert_authorized(user_dict, action, msg, **kwargs):
    """
    Assert that a user is authorized to perform an action.

    Raises an ``AssertionError`` if access was denied.
    """
    context = {'user': user_dict['name']}
    try:
        call_action_with_auth(action, context, **kwargs)
    except NotAuthorized:
        raise AssertionError(msg)


def assert_not_authorized(user_dict, action, msg, **kwargs):
    """
    Assert that a user is not authorized to perform an action.

    Raises an ``AssertionError`` if access was granted.
    """
    context = {'user': user_dict['name']}
    try:
        call_action_with_auth(action, context, **kwargs)
    except NotAuthorized:
        return
    raise AssertionError(msg)


def assert_anonymous_access(action, **kwargs):
    """
    Assert that an action can be called anonymously.
    """
    context = {'user': ''}
    try:
        call_action_with_auth(action, context, **kwargs)
    except NotAuthorized:
        raise AssertionError('"{}" cannot be called anonymously.'.format(
                             action))


def assert_no_anonymous_access(action, **kwargs):
    """
    Assert that an action cannot be called anonymously.
    """
    context = {'user': ''}
    try:
        call_action_with_auth(action, context, **kwargs)
    except NotAuthorized:
        return
    raise AssertionError('"{}" can be called anonymously.'.format(action))


def assert_validation_fails(action, msg=None, **kwargs):
    """
    Assert that an action call doesn't validate.
    """
    try:
        call_action(action, **kwargs)
    except ValidationError:
        return
    if msg is None:
        msg = ('Validation succeeded unexpectedly for action "{action}" with '
               + 'input {input!r}.').format(action=action, input=kwargs)
    raise AssertionError(msg)


class AddressReuseServer(TCPServer):
    allow_reuse_address = True


class HTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Serves files from a given directory instead of current directory.
    """
    def __init__(self, dir, *args, **kwargs):
        self.dir = os.path.abspath(dir)
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    def translate_path(self, path):
        return os.path.join(self.dir, path.lstrip('/'))


class SimpleServer(Thread):
    """
    HTTP server that serves a directory in a separate thread.

    If ``dir`` is not given the current directory is used.
    """
    def __init__(self, dir=None, port=8000):
        super(SimpleServer, self).__init__()
        if dir is None:
            dir = os.getcwd()

        def factory(*args, **kwargs):
            return HTTPRequestHandler(dir, *args, **kwargs)

        self.httpd = AddressReuseServer(("", port), factory)

    def run(self):
        try:
            self.httpd.serve_forever()
        finally:
            self.httpd.server_close()

    def stop(self):
        self.httpd.shutdown()


def assert_time_span(start, stop=None, min=None, max=None):
    """
    Assert validity of a time span.

    ``start`` and ``stop`` are ``datetime.datetime`` instances. If
    ``stop`` is not given the current date and time is used.

    The length of the time span between ``start`` and ``stopped`` is
    computed (in seconds). If ``min`` (``max``) is given and larger
    (smaller) than the time span then an ``AssertionError`` is raised.
    """
    if stop is None:
        stop = datetime.datetime.now()
    span = (stop - start).total_seconds()
    if (min is not None) and (min > span):
        msg = 'Time span {span}s is too small (must be >={min}s).'.format(
            span=span, min=min)
        raise AssertionError(msg)
    if (max is not None) and (max < span):
        msg = 'Time span {span}s is too large (must be <={max}s).'.format(
            span=span, max=max)
        raise AssertionError(max)


def is_package_found(query, pkg_id):
    """
    Check if a package is found via a query.
    """
    result = call_action('package_search', q=query)
    return any(pkg['id'] == pkg_id for pkg in result['results'])


def assert_package_found(query, id, msg=None):
    """
    Assert that a package is found via a query.
    """
    assert_true(is_package_found(query, id), msg)


def assert_package_not_found(query, id, msg=None):
    """
    Assert that a package is not found via a query.
    """
    assert_false(is_package_found(query, id), msg)


try:
    from ckan.tests.helpers import recorded_logs
except ImportError:
    import collections
    import logging

    # Copied from CKAN 2.7
    @contextlib.contextmanager
    def recorded_logs(logger=None, level=logging.DEBUG,
                      override_disabled=True, override_global_level=True):
        u'''
        Context manager for recording log messages.

        :param logger: The logger to record messages from. Can either be a
            :py:class:`logging.Logger` instance or a string with the
            logger's name. Defaults to the root logger.

        :param int level: Temporary log level for the target logger while
            the context manager is active. Pass ``None`` if you don't want
            the level to be changed. The level is automatically reset to its
            original value when the context manager is left.

        :param bool override_disabled: A logger can be disabled by setting
            its ``disabled`` attribute. By default, this context manager
            sets that attribute to ``False`` at the beginning of its
            execution and resets it when the context manager is left. Set
            ``override_disabled`` to ``False`` to keep the current value
            of the attribute.

        :param bool override_global_level: The ``logging.disable`` function
            allows one to install a global minimum log level that takes
            precedence over a logger's own level. By default, this context
            manager makes sure that the global limit is at most ``level``,
            and reduces it if necessary during its execution. Set
            ``override_global_level`` to ``False`` to keep the global limit.

        :returns: A recording log handler that listens to ``logger`` during
            the execution of the context manager.
        :rtype: :py:class:`RecordingLogHandler`

        Example::

            import logging

            logger = logging.getLogger(__name__)

            with recorded_logs(logger) as logs:
                logger.info(u'Hello, world!')

            logs.assert_log(u'info', u'world')
        '''
        if logger is None:
            logger = logging.getLogger()
        elif not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)
        handler = RecordingLogHandler()
        old_level = logger.level
        manager_level = logger.manager.disable
        disabled = logger.disabled
        logger.addHandler(handler)
        try:
            if level is not None:
                logger.setLevel(level)
            if override_disabled:
                logger.disabled = False
            if override_global_level:
                if (level is None) and (manager_level > old_level):
                    logger.manager.disable = old_level
                elif (level is not None) and (manager_level > level):
                    logger.manager.disable = level
            yield handler
        finally:
            logger.handlers.remove(handler)
            logger.setLevel(old_level)
            logger.disabled = disabled
            logger.manager.disable = manager_level


    # Copied from CKAN 2.7
    class RecordingLogHandler(logging.Handler):
        u'''
        Log handler that records log messages for later inspection.

        You can inspect the recorded messages via the ``messages`` attribute
        (a dict that maps log levels to lists of messages) or by using
        ``assert_log``.

        This class is rarely useful on its own, instead use
        :py:func:`recorded_logs` to temporarily record log messages.
        '''
        def __init__(self, *args, **kwargs):
            super(RecordingLogHandler, self).__init__(*args, **kwargs)
            self.clear()

        def emit(self, record):
            self.messages[record.levelname.lower()].append(record.getMessage())

        def assert_log(self, level, pattern, msg=None):
            u'''
            Assert that a certain message has been logged.

            :param string pattern: A regex which the message has to match.
                The match is done using ``re.search``.

            :param string level: The message level (``'debug'``, ...).

            :param string msg: Optional failure message in case the expected
                log message was not logged.

            :raises AssertionError: If the expected message was not logged.
            '''
            compiled_pattern = re.compile(pattern)
            for log_msg in self.messages[level]:
                if compiled_pattern.search(log_msg):
                    return
            if not msg:
                if self.messages[level]:
                    lines = u'\n    '.join(self.messages[level])
                    msg = (u'Pattern "{}" was not found in the log messages for '
                           + u'level "{}":\n    {}').format(pattern, level, lines)
                else:
                    msg = (u'Pattern "{}" was not found in the log messages for '
                           + u'level "{}" (no messages were recorded for that '
                           + u'level).').format(pattern, level)
            raise AssertionError(msg)

        def clear(self):
            u'''
            Clear all captured log messages.
            '''
            self.messages = collections.defaultdict(list)

