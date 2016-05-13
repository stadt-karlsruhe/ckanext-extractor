#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import datetime

import mock

from ckan.model import Package
from ckan.lib.search import index_for
from ckan.tests import factories, helpers
from ckan.lib.celery_app import celery

from .helpers import (assert_equal, get_metadata, assert_no_metadata,
                      assert_package_found, assert_package_not_found)
from ..model import ResourceMetadata
from ..plugin import ExtractorPlugin


RES_DICT =  {
    'url': 'does-not-matter',
    'format': 'pdf',
}

METADATA =  {
    'contents': 'foobar',
    'author': 'john_doe',
    'created': 'yesterday',
}


def send_task(name, args, **opts):
    res_dict = args[1]
    metadata = get_metadata(res_dict)
    metadata.last_format = res_dict['format']
    metadata.last_url = res_dict['url']
    metadata.last_extracted = datetime.datetime.now()
    metadata.task_id = None
    metadata.meta.update(METADATA)
    metadata.save()
    pkg_dict = helpers.call_action('package_show', id=res_dict['package_id'])
    index_for('package').update_dict(pkg_dict)


@mock.patch.object(celery, 'send_task', side_effect=send_task)
class TestHooks(helpers.FunctionalTestBase):
    """
    Test that extraction and indexing happens automatically.
    """
    def test_extraction_upon_resource_creation(self, send_task):
        """
        Metadata is extracted and indexed after resource creation.
        """
        factories.Resource(**RES_DICT)
        assert_equal(send_task.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_extraction_upon_resource_update(self, send_task):
        """
        Metadata is extracted and indexed after resource update.
        """
        res_dict = factories.Resource(**RES_DICT)
        send_task.reset_mock()
        res_dict['format'] = 'doc'  # Change format to trigger new extraction
        helpers.call_action('resource_update', **res_dict)
        assert_equal(send_task.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_deletion_upon_resource_deletion(self, send_task):
        """
        Metadata is removed when a resource is deleted.
        """
        res_dict = factories.Resource(**RES_DICT)
        assert_package_found(METADATA['contents'], res_dict['package_id'],
                             'Metadata not added to index.')
        assert_package_found(METADATA['author'], res_dict['package_id'],
                             'Metadata not added to index.')
        helpers.call_action('resource_delete', {'ignore_auth': True}, **res_dict)
        assert_package_not_found(METADATA['contents'], res_dict['package_id'],
                                 'Metadata not removed from index.')
        assert_package_not_found(METADATA['author'], res_dict['package_id'],
                                 'Metadata not removed from index.')
        assert_no_metadata(res_dict)

    def test_resource_deletion_with_no_metadata(self, send_task):
        """
        A resource that doesn't have metadata can be removed.
        """
        res_dict = factories.Resource(url='foo', format='not-indexed')
        helpers.call_action('resource_delete', {'ignore_auth': True}, **res_dict)

