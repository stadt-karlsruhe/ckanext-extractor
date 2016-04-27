#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import mock
from nose.tools import assert_false, assert_raises, assert_true

from ckan.logic import NotFound
from ckan.model import Resource
from ckan.tests.helpers import call_action, FunctionalTestBase
from ckan.tests import factories

from ...model import ResourceMetadata
from ..helpers import (assert_equal, assert_no_metadata, get_metadata,
                       fake_process)


class TestMetadataList(FunctionalTestBase):

    def test_metadata_list_empty(self):
        """
        metadata_list when no metadata exist.
        """
        assert_equal(call_action('extractor_metadata_list'), [])

    def test_metadata_list_inprogress(self):
        """
        metadata_list does not list metadata that is in progress.
        """
        factories.Resource(format='pdf')
        assert_equal(call_action('extractor_metadata_list'), [])

    def test_metadata_list_some(self):
        """
        metadata_list when some metadata exist.
        """
        res_dict = factories.Resource(format='pdf')
        fake_process(res_dict)
        assert_equal(call_action('extractor_metadata_list'), [res_dict['id']])


@mock.patch('ckan.lib.celery_app.celery.send_task')
class TestMetadataExtract(FunctionalTestBase):

    def test_metadata_extract_new_indexed(self, send_task):
        """
        metadata_extract for a new resource with indexed format.
        """
        res_dict = factories.Resource(format='pdf')
        get_metadata(res_dict).delete().commit()
        send_task.reset_mock()
        result = call_action('extractor_metadata_extract', id=res_dict['id'])
        assert_equal(result['status'], 'new', 'Wrong state')
        assert_false(result['task_id'] is None, 'Missing task ID')
        assert_equal(result['task_id'], get_metadata(res_dict).task_id,
                     'Task IDs differ.')
        assert_equal(send_task.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_metadata_extract_new_ignored(self, send_task):
        """
        metadata_extract for a new resource with ignored format.
        """
        res_dict = factories.Resource(format='foo')
        result = call_action('extractor_metadata_extract', id=res_dict['id'])
        assert_equal(result['status'], 'ignored', 'Wrong state')
        assert_true(result['task_id'] is None, 'Unexpected task ID')
        assert_equal(send_task.call_count, 0,
                     'Wrong number of extraction tasks.')

    def test_metadata_extract_unchanged(self, send_task):
        """
        metadata_extract for a resource with unchanged format and URL.
        """
        res_dict = factories.Resource(format='pdf')
        send_task.reset_mock()
        fake_process(res_dict)
        result = call_action('extractor_metadata_extract', id=res_dict['id'])
        assert_equal(result['status'], 'unchanged', 'Wrong state')
        assert_true(result['task_id'] is None, 'Unexpected task ID')
        assert_equal(result['task_id'], get_metadata(res_dict).task_id,
                     'Task IDs differ.')
        assert_equal(send_task.call_count, 0,
                     'Wrong number of extraction tasks.')

    def test_metadata_extract_update_indexed_format(self, send_task):
        """
        metadata_extract for a resource with updated, indexed format.
        """
        res_dict = factories.Resource(format='pdf')
        send_task.reset_mock()
        fake_process(res_dict)

        resource = Resource.get(res_dict['id'])
        resource.format = 'doc'
        resource.save()

        result = call_action('extractor_metadata_extract', id=res_dict['id'])
        assert_equal(result['status'], 'update', 'Wrong state')
        assert_false(result['task_id'] is None, 'Missing task ID')
        assert_equal(result['task_id'], get_metadata(res_dict).task_id,
                     'Task IDs differ.')
        assert_equal(send_task.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_metadata_extract_update_ignored_format(self, send_task):
        """
        metadata_extract for a resource with updated, ignored format.
        """
        res_dict = factories.Resource(format='pdf')
        send_task.reset_mock()
        fake_process(res_dict)

        resource = Resource.get(res_dict['id'])
        resource.format = 'foo'
        resource.save()

        result = call_action('extractor_metadata_extract', id=res_dict['id'])
        assert_equal(result['status'], 'ignored', 'Wrong state')
        assert_true(result['task_id'] is None, 'Unexpected task ID')
        assert_equal(send_task.call_count, 0,
                     'Wrong number of extraction tasks.')
        assert_no_metadata(res_dict)

    def test_metadata_extract_inprogress(self, send_task):
        """
        metadata_extract for a resource that's already being extracted.
        """
        res_dict = factories.Resource(format='pdf')
        send_task.reset_mock()
        old_task_id = get_metadata(res_dict).task_id
        result = call_action('extractor_metadata_extract', id=res_dict['id'])
        assert_equal(result['status'], 'inprogress', 'Wrong state')
        assert_equal(result['task_id'], old_task_id, 'Task IDs differ.')
        assert_equal(send_task.call_count, 0,
                     'Wrong number of extraction tasks.')

    def test_metadata_extract_unexisting(self, send_task):
        """
        metadata_extract for a resource that does not exist.
        """
        assert_raises(
            NotFound, lambda: call_action('extractor_metadata_extract',
            id='does-not-exist'))

