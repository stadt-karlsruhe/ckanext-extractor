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

from collections import defaultdict
import functools
import requests

import mock
from pylons import config

from ckan.tests import factories, helpers
from ckan.plugins import implements, SingletonPlugin, PluginImplementations

from ..interfaces import IExtractorPostprocessor, IExtractorRequest
from ..tasks import extract
from .helpers import (assert_equal, get_metadata, assert_package_found,
                      assert_package_not_found)
from nose.tools import assert_true


RES_DICT =  {
    'url': 'https://does-not-matter',
    'format': 'PDF',
}

METADATA =  {
    'fulltext': 'foobar',
    'author': 'john_doe',
    'created': 'yesterday',
}


def filter_metadata(d):
    keys = config['ckanext.extractor.indexed_fields'].split()
    return dict((key, value) for key, value in d.iteritems() if key in keys)


class MockPostprocessor(SingletonPlugin):

    def __init__(self):
        SingletonPlugin.__init__(self)
        self.called = 0


class MockAfterExtractPostprocessor(MockPostprocessor):
    implements(IExtractorPostprocessor, inherit=True)

    def extractor_after_extract(self, res_dict, extracted):
        self.called += 1
        for key, value in RES_DICT.iteritems():
            assert_equal(value, res_dict[key])
        assert_equal(extracted, METADATA)
        extracted['fulltext'] = 'i can change this'


class MockAfterSavePostprocessor(MockPostprocessor):
    implements(IExtractorPostprocessor, inherit=True)

    def extractor_after_save(self, res_dict, metadata_dict):
        self.called += 1
        for key, value in RES_DICT.iteritems():
            assert_equal(value, res_dict[key])
        assert_equal(metadata_dict['meta'], filter_metadata(METADATA))
        assert_package_not_found(METADATA['fulltext'], res_dict['package_id'])


class MockAfterIndexPostprocessor(MockPostprocessor):
    implements(IExtractorPostprocessor, inherit=True)

    def extractor_after_index(self, res_dict, metadata_dict):
        self.called += 1
        for key, value in RES_DICT.iteritems():
            assert_equal(value, res_dict[key])
        assert_equal(metadata_dict['meta'], filter_metadata(METADATA))
        assert_package_found(METADATA['fulltext'], res_dict['package_id'])


class MockBeforeRequest(MockPostprocessor):
    implements(IExtractorRequest, inherit=True)

    def extractor_before_request(self, request):
        self.called += 1
        assert_true(isinstance(request, requests.PreparedRequest))
        request.url = 'http://test-url.example.com/file.pdf'
        return request


MockPostprocessor().disable()
MockAfterExtractPostprocessor().disable()
MockAfterSavePostprocessor().disable()
MockAfterIndexPostprocessor().disable()
MockBeforeRequest().disable()


def with_plugin(cls):
    '''
    Activate a plugin during a function's execution.
    '''
    def decorator(f):
        plugin = cls()
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            plugin.activate()
            try:
                plugin.enable()
                args = list(args) + [plugin]
                return f(*args, **kwargs)
            finally:
                plugin.disable()
        return wrapped
    return decorator


@mock.patch('ckanext.extractor.tasks.load_config')
@mock.patch('ckanext.extractor.tasks.download_and_extract',
            side_effect=lambda _: METADATA.copy())
class TestIExtractorPostprocessor(object):

    @with_plugin(MockAfterExtractPostprocessor)
    def test_after_extract(self, download_and_extract, load_config, plugin):
        res_dict = factories.Resource(**RES_DICT)
        get_metadata(res_dict).delete().commit()
        extract(config['__file__'], res_dict)
        assert_equal(plugin.called, 1)
        metadata = get_metadata(res_dict)
        assert_equal(metadata.meta['fulltext'], 'i can change this')

    @with_plugin(MockAfterSavePostprocessor)
    def test_after_save(self, download_and_extract, load_config, plugin):
        res_dict = factories.Resource(**RES_DICT)
        get_metadata(res_dict).delete().commit()
        extract(config['__file__'], res_dict)
        assert_equal(plugin.called, 1)

    @with_plugin(MockAfterIndexPostprocessor)
    def test_after_index(self, download_and_extract, load_config, plugin):
        res_dict = factories.Resource(**RES_DICT)
        get_metadata(res_dict).delete().commit()
        extract(config['__file__'], res_dict)
        assert_equal(plugin.called, 1)

@mock.patch('ckanext.extractor.tasks.load_config')
@mock.patch('ckanext.extractor.tasks.toolkit')
@mock.patch('ckanext.extractor.tasks.index_for')
@mock.patch('ckanext.extractor.lib.pysolr.Solr')
@mock.patch('ckanext.extractor.lib.Session')
class TestIExtractorRequest(object):

    def setup(self):
        self.res_dict = factories.Resource(**RES_DICT)

    @with_plugin(MockBeforeRequest)
    def test_before_request(self, session, solr, index_for, toolkit, load_config, plugin):
        extract(config['__file__'], self.res_dict)
        assert_equal(plugin.called, 1)
        assert_true(session.called)
        
        name, args, kwargs = session.mock_calls[1]
        assert_equal(name, '().send')
        assert_equal(args[0].url, 'http://test-url.example.com/file.pdf')
