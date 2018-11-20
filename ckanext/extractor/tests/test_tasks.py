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
import logging
import re

import mock
from pylons import config
from nose.tools import assert_false, assert_true
from requests.exceptions import RequestException

from ckan.lib import search
from ckan.plugins import toolkit
from ckan.tests import factories
from ckan.tests.helpers import FunctionalTestBase

from ..tasks import extract
from .helpers import (assert_equal, assert_time_span, get_metadata,
                      assert_package_found, assert_package_not_found,
                      recorded_logs)


RES_DICT =  {
    'url': 'does-not-matter',
    'format': 'pdf',
}

METADATA =  {
    'fulltext': 'foobar',
    'author': 'john_doe',
    'created': 'yesterday',
}


@mock.patch('ckanext.extractor.tasks.download_and_extract',
            return_value=METADATA)
@mock.patch('ckanext.extractor.tasks.load_config')
class TestMetadataExtractTask(FunctionalTestBase):

    def test_new(self, lc_mock, dae_mock):
        """
        Metadata extraction without previous metadata.
        """
        res_dict = factories.Resource(**RES_DICT)
        get_metadata(res_dict).delete().commit()
        extract(config['__file__'], res_dict)
        metadata = get_metadata(res_dict)
        assert_equal(metadata.meta['fulltext'], METADATA['fulltext'],
                     'Wrong fulltext.')
        assert_equal(metadata.meta['author'], METADATA['author'],
                     'Wrong author.')
        assert_false('created' in metadata.meta,
                     '"created" field was not ignored.')
        assert_equal(metadata.last_format, res_dict['format'],
                     'Wrong last_format')
        assert_equal(metadata.last_url, res_dict['url'], 'Wrong last_url.')
        assert_true(metadata.task_id is None, 'Unexpected task ID.')
        assert_time_span(metadata.last_extracted, max=5)
        assert_package_found(METADATA['fulltext'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_found(METADATA['author'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_not_found(METADATA['created'], res_dict['package_id'],
                                 'Wrong metadata indexed.')

    def test_update(self, lc_mock, dae_mock):
        """
        Metadata extraction of indexed format with previous metadata.
        """
        res_dict = factories.Resource(**RES_DICT)
        metadata = get_metadata(res_dict)
        metadata.meta['fulltext'] = 'old fulltext'
        metadata.meta['author'] = 'old author'
        metadata.meta['updated'] = 'should be removed'
        metadata.meta['last_extracted'] = datetime.datetime(2000, 1, 1)
        metadata.last_format = 'old format'
        metadata.last_url = 'old url'
        metadata.save()
        extract(config['__file__'], res_dict)
        metadata = get_metadata(res_dict)
        assert_equal(metadata.meta['fulltext'], METADATA['fulltext'],
                     'Wrong fulltext.')
        assert_equal(metadata.meta['author'], METADATA['author'],
                     'Wrong author.')
        assert_false('created' in metadata.meta,
                     '"created" field was not ignored.')
        assert_false('updated' in metadata.meta,
                     '"updated" field was not removed.')
        assert_equal(metadata.last_format, res_dict['format'],
                     'Wrong last_format')
        assert_equal(metadata.last_url, res_dict['url'], 'Wrong last_url.')
        assert_true(metadata.task_id is None, 'Unexpected task ID.')
        assert_time_span(metadata.last_extracted, max=5)
        assert_package_found(METADATA['fulltext'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_found(METADATA['author'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_not_found(METADATA['created'], res_dict['package_id'],
                                 'Wrong metadata indexed.')

    def test_download_errors(self, lc_mock, dae_mock):
        """
        Handling of errors during resource downloading.
        """
        dae_mock.side_effect = RequestException('OH NOES')
        res_dict = factories.Resource(**RES_DICT)
        with recorded_logs() as logs:
            extract(config['__file__'], res_dict)
        logs.assert_log('warning', re.escape(res_dict['url']))
        logs.assert_log('warning', 'OH NOES')

    def test_extraction_from_private_dataset(self, lc_mock, dae_mock):
        """
        Handling of resources in private datasets.
        """
        # See https://github.com/stadt-karlsruhe/ckanext-extractor/issues/8
        org_dict = factories.Organization()
        pkg_dict = factories.Dataset(private=True, owner_org=org_dict['id'])
        res_dict = factories.Resource(package_id=pkg_dict['id'], **RES_DICT)
        with recorded_logs() as logs:
            extract(config['__file__'], res_dict)
        logs.assert_log('debug', 'private')
        dae_mock.assert_not_called()

    def test_multiple_values_for_the_same_field(self, lc_mock, dae_mock):
        """
        Handling of multiple values for the same metadata field.
        """
        # See https://github.com/stadt-karlsruhe/ckanext-extractor/issues/11
        dae_mock.return_value = {
            'fulltext': 'foobar',
            'author': ['john_doe', 'jane_doe'],
        }
        res_dict = factories.Resource(**RES_DICT)
        with recorded_logs() as logs:
            extract(config['__file__'], res_dict)
        logs.assert_log('debug', 'Collapsing.*author')
        metadata = get_metadata(res_dict)
        assert_equal(metadata.meta['author'], 'john_doe, jane_doe')

    def test_package_update_race_condition(self, lc_mock, dae_mock):
        """
        Handling of package updates during extraction.
        """
        res_dict = factories.Resource(**RES_DICT)
        sysadmin = factories.Sysadmin()

        def download_and_extract(*args, **kwargs):
            # Simulate a change to the package by another party during
            # the download and extraction process.
            toolkit.get_action('package_patch')({'user': sysadmin['name']},
                                                {'id': res_dict['package_id'],
                                                 'title': 'A changed title'})
            return {'fulltext': 'foobar'}

        dae_mock.side_effect = download_and_extract
        extract(config['__file__'], res_dict)

        # Make sure that the changed package metadata is kept and indexed
        pkg_dict = toolkit.get_action('package_show')(
                {}, {'id': res_dict['package_id']})
        assert_equal(pkg_dict['title'], 'A changed title')
        indexed_pkg_dict = search.show(res_dict['package_id'])
        assert_equal(indexed_pkg_dict['title'], 'A changed title')

