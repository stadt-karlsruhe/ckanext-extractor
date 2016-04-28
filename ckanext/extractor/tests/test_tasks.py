#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import datetime

import mock
from pylons import config
from nose.tools import assert_false, assert_true

from ckan.tests import factories

from ..tasks import metadata_extract
from .helpers import assert_equal, assert_time_span, get_metadata


RES_DICT =  {
    'id': 'my-id',
    'url': 'does-not-matter',
    'format': 'pdf',
}

METADATA =  {
    'contents': 'Foobar',
    'author': 'John Doe',
    'created': 'yesterday',
}

def download_and_extract_mock(*args, **kwargs):
    return METADATA


@mock.patch('ckanext.extractor.tasks.download_and_extract',
            new=download_and_extract_mock)
class TestMetadataExtractTask(object):

    def test_new(self):
        """
        Metadata extraction without previous metadata.
        """
        metadata_extract(config['__file__'], RES_DICT)
        metadata = get_metadata(RES_DICT)
        assert_equal(metadata.meta['contents'], METADATA['contents'],
                     'Wrong contents.')
        assert_equal(metadata.meta['author'], METADATA['author'],
                     'Wrong author.')
        assert_false('created' in metadata.meta,
                     '"created" field was not ignored.')
        assert_equal(metadata.last_format, RES_DICT['format'],
                     'Wrong last_format')
        assert_equal(metadata.last_url, RES_DICT['url'], 'Wrong last_url.')
        assert_true(metadata.task_id is None, 'Unexpected task ID.')
        assert_time_span(metadata.last_extracted, max=5)

    @mock.patch('ckan.lib.celery_app.celery.send_task')
    def test_update(self, send_task):
        """
        Metadata extraction of indexed format with previous metadata.
        """
        factories.Resource(**RES_DICT)
        metadata = get_metadata(RES_DICT)
        metadata.meta['contents'] = 'old contents'
        metadata.meta['author'] = 'old author'
        metadata.meta['updated'] = 'should be removed'
        metadata.meta['last_extracted'] = datetime.datetime(2000, 1, 1)
        metadata.last_format = 'old format'
        metadata.last_url = 'old url'
        metadata.save()
        metadata_extract(config['__file__'], RES_DICT)
        metadata = get_metadata(RES_DICT)
        assert_equal(metadata.meta['contents'], METADATA['contents'],
                     'Wrong contents.')
        assert_equal(metadata.meta['author'], METADATA['author'],
                     'Wrong author.')
        assert_false('created' in metadata.meta,
                     '"created" field was not ignored.')
        assert_false('updated' in metadata.meta,
                     '"updated" field was not removed.')
        assert_equal(metadata.last_format, RES_DICT['format'],
                     'Wrong last_format')
        assert_equal(metadata.last_url, RES_DICT['url'], 'Wrong last_url.')
        assert_true(metadata.task_id is None, 'Unexpected task ID.')
        assert_time_span(metadata.last_extracted, max=5)

