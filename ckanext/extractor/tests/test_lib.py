#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 Stadt Karlsruhe (www.karlsruhe.de)
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
        assert_true('Foobarium' in metadata['fulltext'], 'Incorrect fulltext.')
        assert_equal(metadata['content-type'], 'application/pdf')


def test_clean_metadatum():
    assert_equal(clean_metadatum('X_y', ['X_y']), ('x-y', 'X_y'))

