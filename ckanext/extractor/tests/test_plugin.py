#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 Stadt Karlsruhe (www.karlsruhe.de)
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

import mock
from sqlalchemy.orm.exc import NoResultFound

from ckan.model import Package
from ckan.lib.search import index_for
from ckan.tests import factories, helpers

from .helpers import (assert_equal, get_metadata, assert_metadata,
                      assert_no_metadata, assert_package_found,
                      assert_package_not_found)
from ..model import ResourceMetadata
from ..plugin import ExtractorPlugin


RES_DICT =  {
    'url': 'does-not-matter',
    'format': 'pdf',
}

METADATA =  {
    'fulltext': 'foobar',
    'author': 'john_doe',
    'created': 'yesterday',
}


def enqueue_job(name, args, **opts):
    res_dict = args[1]
    try:
        metadata = get_metadata(res_dict)
    except NoResultFound:
        metadata = ResourceMetadata.create(resource_id=res_dict['id'])
    metadata.last_format = res_dict['format']
    metadata.last_url = res_dict['url']
    metadata.last_extracted = datetime.datetime.now()
    metadata.task_id = None
    metadata.meta.update(METADATA)
    metadata.save()
    pkg_dict = helpers.call_action('package_show', id=res_dict['package_id'])
    index_for('package').update_dict(pkg_dict)
    return mock.Mock(id=None)


@mock.patch('ckanext.extractor.logic.action.enqueue_job',
            side_effect=enqueue_job)
class TestHooks(helpers.FunctionalTestBase):
    """
    Test that extraction and indexing happens automatically.
    """
    def test_extraction_upon_resource_creation(self, enqueue_job):
        """
        Metadata is extracted and indexed after resource creation.
        """
        factories.Resource(**RES_DICT)
        assert_equal(enqueue_job.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_extraction_upon_resource_update(self, enqueue_job):
        """
        Metadata is extracted and indexed after resource update.
        """
        res_dict = factories.Resource(**RES_DICT)
        enqueue_job.reset_mock()
        res_dict['format'] = 'doc'  # Change format to trigger new extraction
        helpers.call_action('resource_update', **res_dict)
        assert_equal(enqueue_job.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_deletion_upon_resource_deletion(self, enqueue_job):
        """
        Metadata is removed when a resource is deleted.
        """
        res_dict = factories.Resource(**RES_DICT)
        assert_package_found(METADATA['fulltext'], res_dict['package_id'],
                             'Metadata not added to index.')
        assert_package_found(METADATA['author'], res_dict['package_id'],
                             'Metadata not added to index.')
        helpers.call_action('resource_delete', **res_dict)
        assert_package_not_found(METADATA['fulltext'], res_dict['package_id'],
                                 'Metadata not removed from index.')
        assert_package_not_found(METADATA['author'], res_dict['package_id'],
                                 'Metadata not removed from index.')
        assert_no_metadata(res_dict)

    def test_resource_deletion_with_no_metadata(self, enqueue_job):
        """
        A resource that doesn't have metadata can be removed.
        """
        res_dict = factories.Resource(url='foo', format='not-indexed')
        helpers.call_action('resource_delete', {'ignore_auth': True}, **res_dict)

    def test_extraction_after_public_dataset_update(self, enqueue_job):
        """
        If a public dataset is updated then its resources are extracted.
        """
        pkg_dict = factories.Dataset()
        res_dict = factories.Resource(package_id=pkg_dict['id'], **RES_DICT)
        pkg_dict = helpers.call_action('package_show', id=pkg_dict['id'])
        helpers.call_action('extractor_delete', id=res_dict['id'])
        enqueue_job.reset_mock()
        helpers.call_action('package_update', **pkg_dict)
        assert_equal(enqueue_job.call_count, 1,
                     'Wrong number of extraction tasks.')

    def test_deletion_after_private_dataset_update(self, enqueue_job):
        """
        If a private dataset is updated its resources' metadata is removed.
        """
        user = factories.Sysadmin()
        org_dict = factories.Organization()
        pkg_dict = factories.Dataset(owner_org=org_dict['id'])
        res_dict = factories.Resource(package_id=pkg_dict['id'], **RES_DICT)
        pkg_dict = helpers.call_action('package_show', id=pkg_dict['id'])
        pkg_dict['private'] = True
        assert_metadata(res_dict)
        helpers.call_action('package_update', {'user': user['id']}, **pkg_dict)
        assert_no_metadata(res_dict)

