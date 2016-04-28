#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os.path

from nose.tools import assert_true

from ..lib import clean_metadatum, download_and_extract
from .helpers import assert_equal, SimpleServer


class TestDownloadAndExtract(object):

    PORT = 8000

    def __init__(self):
        self.server = SimpleServer(os.path.dirname(__file__), self.PORT)

    def setup(self):
        self.server.start()

    def teardown(self):
        self.server.stop()

    def test_download_and_extract(self):
        pdf_url = 'http://localhost:{port}/test.pdf'.format(port=self.PORT)
        metadata = download_and_extract(pdf_url)
        assert_true('Foobarium' in metadata['contents'], 'Incorrect contents.')
        assert_equal(metadata['content-type'], 'application/pdf')


def test_clean_metadatum():
    assert_equal(clean_metadatum('X_y', ['X_y']), ('x-y', 'X_y'))

