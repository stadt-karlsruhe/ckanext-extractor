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
from ..helpers import (assert_anonymous_access, assert_authorized, assert_equal,
                       assert_no_anonymous_access, assert_no_metadata,
                       assert_not_authorized, get_metadata, fake_process,
                       assert_validation_fails)


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

    def test_metadata_list_auth(self):
        """
        Authorization for metadata_show.
        """
        assert_authorized(factories.User(), 'extractor_metadata_list',
                          "Normal user wasn't allowed to metadata_list")
        assert_anonymous_access('extractor_metadata_list')


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

    def test_metadata_extract_auth(self, send_task):
        """
        Authorization for metadata_extract.
        """
        res_dict = factories.Resource(format='pdf')
        assert_not_authorized(factories.User(), 'extractor_metadata_extract',
                             'Normal user was allowed to metadata_extract',
                             id=res_dict['id'])
        assert_no_anonymous_access('extractor_metadata_extract',
                                   id=res_dict['id'])
        assert_authorized(factories.Sysadmin(), 'extractor_metadata_extract',
                          "Sysadmin wasn't allowed to metadata_extract",
                          id=res_dict['id'])

    def test_metadata_extract_validation(self, send_task):
        """
        Input validation for metadata_extract.
        """
        assert_validation_fails('extractor_metadata_extract',
                                'ID was not required.')


@mock.patch('ckan.lib.celery_app.celery.send_task')
class TestMetadataShow(FunctionalTestBase):

    def test_metadata_show_unexisting(self, send_task):
        """
        metadata_show for a resource that does not exist.
        """
        assert_raises(
            NotFound, lambda: call_action('extractor_metadata_show',
            id='does-not-exist'))

    def test_metadata_show_inprogress(self, send_task):
        """
        metadata_show for metadata that is in progress.
        """
        res_dict = factories.Resource(format='pdf')
        task_id = send_task.call_args[1]['task_id']
        result = call_action('extractor_metadata_show', id=res_dict['id'])
        assert_equal(result['task_id'], task_id, 'Wrong task ID.')

    def test_metadata_show_normal(self, send_task):
        """
        metadata_show for normal metadata.
        """
        res_dict = factories.Resource(format='pdf')
        fake_process(res_dict)
        metadata = get_metadata(res_dict)
        metadata.meta['contents'] = 'foobar'
        metadata.meta['author'] = 'John Doe'
        metadata.save()
        result = call_action('extractor_metadata_show', id=res_dict['id'])
        assert_equal(result['meta']['contents'], 'foobar', 'Wrong contents.')
        assert_equal(result['meta']['author'], 'John Doe', 'Wrong author.')
        assert_equal(result['resource_id'], res_dict['id'],
                     'Wrong resource ID.')
        assert_true(result['task_id'] is None, 'Unexpected task ID.')

    def test_metadata_show_auth(self, send_task):
        """
        Authorization for metadata_show.
        """
        res_dict = factories.Resource(format='pdf')
        assert_authorized(factories.User(), 'extractor_metadata_show',
                          "Normal user wasn't allowed to metadata_show",
                          id=res_dict['id'])
        assert_anonymous_access('extractor_metadata_show', id=res_dict['id'])

    def test_metadata_show_validation(self, send_task):
        """
        Input validation for metadata_show.
        """
        assert_validation_fails('extractor_metadata_show',
                                'ID was not required.')


@mock.patch('ckan.lib.celery_app.celery.send_task')
class TestMetadataDelete(FunctionalTestBase):

    def test_metadata_delete_unexisting(self, send_task):
        """
        metadata_delete for a resource that does not exist.
        """
        assert_raises(
            NotFound, lambda: call_action('extractor_metadata_delete',
            id='does-not-exist'))

    def test_metadata_delete_normal(self, send_task):
        """
        metadata_delete for a normal resource.
        """
        res_dict = factories.Resource(format='pdf')
        fake_process(res_dict)
        call_action('extractor_metadata_delete', id=res_dict['id'])
        assert_no_metadata(res_dict)

    def test_metadata_delete_auth(self, send_task):
        """
        Authorization for metadata_delete.
        """
        res_dict = factories.Resource(format='pdf')
        assert_not_authorized(factories.User(), 'extractor_metadata_delete',
                             'Normal user was allowed to metadata_delete',
                             id=res_dict['id'])
        assert_no_anonymous_access('extractor_metadata_delete',
                                   id=res_dict['id'])
        assert_authorized(factories.Sysadmin(), 'extractor_metadata_delete',
                          "Sysadmin wasn't allowed to metadata_delete",
                          id=res_dict['id'])

    def test_metadata_delete_validation(self, send_task):
        """
        Input validation for metadata_delete.
        """
        assert_validation_fails('extractor_metadata_delete',
                                'ID was not required.')

