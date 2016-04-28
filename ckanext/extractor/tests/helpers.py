#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from nose.tools import assert_raises

from ckan.logic import NotAuthorized
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
    context = {'user': user_dict['id']}
    try:
        call_action_with_auth(action, context, **kwargs)
    except NotAuthorized:
        raise AssertionError(msg)


def assert_not_authorized(user_dict, action, msg, **kwargs):
    """
    Assert that a user is not authorized to perform an action.

    Raises an ``AssertionError`` if access was granted.
    """
    context = {'user': user_dict['id']}
    try:
        call_action_with_auth(action, context, **kwargs)
    except NotAuthorized:
        return
    raise AssertionError(msg)

