#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os.path
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer
from threading import Thread

from nose.tools import assert_true

from ..lib import clean_metadatum, download_and_extract
from .helpers import assert_equal


PORT = 8000
HERE = os.path.abspath(os.path.dirname(__file__))
PDF_URL = 'http://localhost:{port}/test.pdf'.format(port=PORT)


class AddressReuseServer(TCPServer):
    allow_reuse_address = True


class HTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Serves files from this directory instead of current directory.
    """
    def translate_path(self, path):
        return os.path.join(HERE, path.lstrip('/'))


class SimpleServer(Thread):
    """
    HTTP server that serves this directory in a separate thread.
    """
    def __init__(self):
        super(SimpleServer, self).__init__()
        self.httpd = AddressReuseServer(("", PORT), HTTPRequestHandler)

    def run(self):
        try:
            self.httpd.serve_forever()
        finally:
            self.httpd.server_close()

    def stop(self):
        self.httpd.shutdown()


class TestDownloadAndExtract(object):

    def __init__(self):
        self.server = SimpleServer()

    def setup(self):
        self.server.start()

    def teardown(self):
        self.server.stop()

    def test_download_and_extract(self):
        metadata = download_and_extract(PDF_URL)
        assert_true('Foobarium' in metadata['contents'], 'Incorrect contents.')
        assert_equal(metadata['content-type'], 'application/pdf')


def test_clean_metadatum():
    assert_equal(clean_metadatum('X_y', ['X_y']), ('x-y', 'X_y'))

