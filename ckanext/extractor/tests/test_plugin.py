#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import mock

from ckan.tests import factories, helpers

from ..model import ResourceMetadata


def assert_equals(got, expected, msg=''):
    """
    Assert that two values are equal.
    """
    if got == expected:
        return
    msg = (msg + ' Expected {!r} but got {!r}.'.format(expected, got)).strip()
    raise AssertionError(msg)


def _send_task(name, args, **kwargs):
    """
    Mock for ``ckan.lib.celery_app.celery.send_task``.
    """
    resource = args[1]
    metadata = ResourceMetadata.one(resource_id=resource['id'])
    metadata.task_id = None  # Mark as processed


@mock.patch('ckan.lib.celery_app.celery.send_task', wraps=_send_task)
class TestHooks(helpers.FunctionalTestBase):
    """
    Test that extraction and indexing happens automatically.
    """
    def test_extraction_upon_resource_creation(self, send_task):
        """
        Metadata is extracted and indexed after resource creation.
        """
        factories.Resource(format='pdf')
        assert_equals(send_task.call_count, 1, 'Wrong number of extraction tasks.')

    def test_extraction_upon_resource_update(self, send_task):
        """
        Metadata is extracted and indexed after resource update.
        """
        resource = factories.Resource(format='pdf')
        send_task.reset_mock()
        resource['description'] = 'A new description!'
        helpers.call_action('resource_update', **resource)
        assert_equals(send_task.call_count, 1, 'Wrong number of extraction tasks.')

