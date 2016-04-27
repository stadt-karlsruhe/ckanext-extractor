#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import mock

from ckan.tests import factories, helpers

from .helpers import assert_equal, fake_process


@mock.patch('ckan.lib.celery_app.celery.send_task')
class TestHooks(helpers.FunctionalTestBase):
    """
    Test that extraction and indexing happens automatically.
    """
    def test_extraction_upon_resource_creation(self, send_task):
        """
        Metadata is extracted and indexed after resource creation.
        """
        factories.Resource(format='pdf')
        assert_equal(send_task.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_extraction_upon_resource_update(self, send_task):
        """
        Metadata is extracted and indexed after resource update.
        """
        resource = factories.Resource(format='pdf')
        send_task.reset_mock()
        fake_process(resource)
        resource['format'] = 'doc'  # Change format to trigger new extraction
        helpers.call_action('resource_update', **resource)
        assert_equal(send_task.call_count, 1,
                     'Wrong number of extraction tasks.')

