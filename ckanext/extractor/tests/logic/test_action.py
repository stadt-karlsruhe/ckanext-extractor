#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from nose.tools import assert_equals

from ckan.tests.helpers import call_action, FunctionalTestBase


class TestAction(FunctionalTestBase):

    #
    # extractor_metadata_list
    #

    def test_metadata_list_returns_list(self):
        assert_equals(call_action('extractor_metadata_list'), [])

