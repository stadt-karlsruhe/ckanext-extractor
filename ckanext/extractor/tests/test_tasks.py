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

import mock
from pylons import config
from nose.tools import assert_false, assert_true

from ckan.tests import factories

from ..tasks import extract
from .helpers import (assert_equal, assert_time_span, get_metadata,
                      assert_package_found, assert_package_not_found)


RES_DICT =  {
    'url': 'does-not-matter',
    'format': 'pdf',
}

METADATA =  {
    'contents': 'foobar',
    'author': 'john_doe',
    'created': 'yesterday',
}


@mock.patch('ckanext.extractor.tasks.download_and_extract',
            return_value=METADATA)
class TestMetadataExtractTask(object):

    def test_new(self, _):
        """
        Metadata extraction without previous metadata.
        """
        res_dict = factories.Resource(**RES_DICT)
        get_metadata(res_dict).delete().commit()
        extract(config['__file__'], res_dict)
        metadata = get_metadata(res_dict)
        assert_equal(metadata.meta['contents'], METADATA['contents'],
                     'Wrong contents.')
        assert_equal(metadata.meta['author'], METADATA['author'],
                     'Wrong author.')
        assert_false('created' in metadata.meta,
                     '"created" field was not ignored.')
        assert_equal(metadata.last_format, res_dict['format'],
                     'Wrong last_format')
        assert_equal(metadata.last_url, res_dict['url'], 'Wrong last_url.')
        assert_true(metadata.task_id is None, 'Unexpected task ID.')
        assert_time_span(metadata.last_extracted, max=5)
        assert_package_found(METADATA['contents'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_found(METADATA['author'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_not_found(METADATA['created'], res_dict['package_id'],
                                 'Wrong metadata indexed.')

    def test_update(self, _):
        """
        Metadata extraction of indexed format with previous metadata.
        """
        res_dict = factories.Resource(**RES_DICT)
        metadata = get_metadata(res_dict)
        metadata.meta['contents'] = 'old contents'
        metadata.meta['author'] = 'old author'
        metadata.meta['updated'] = 'should be removed'
        metadata.meta['last_extracted'] = datetime.datetime(2000, 1, 1)
        metadata.last_format = 'old format'
        metadata.last_url = 'old url'
        metadata.save()
        extract(config['__file__'], res_dict)
        metadata = get_metadata(res_dict)
        assert_equal(metadata.meta['contents'], METADATA['contents'],
                     'Wrong contents.')
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
        assert_package_found(METADATA['contents'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_found(METADATA['author'], res_dict['package_id'],
                             'Metadata not indexed.')
        assert_package_not_found(METADATA['created'], res_dict['package_id'],
                                 'Wrong metadata indexed.')

