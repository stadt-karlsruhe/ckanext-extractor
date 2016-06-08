#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016 Stadt Karlsruhe (www.karlsruhe.de)
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

import datetime
import os.path
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

