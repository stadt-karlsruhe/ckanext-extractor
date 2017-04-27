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
import tempfile

from ckan.plugins import PluginImplementations
from .interfaces import IExtractorRequest

from pylons import config
import pysolr
from requests import Request, Session


def download_and_extract(resource_url):
    """
    Download resource and extract metadata using Solr.

    The extracted metadata is cleaned and returned.
    """
    session = Session()
    request = Request('GET', resource_url).prepare()
    for plugin in PluginImplementations(IExtractorRequest):
        request = plugin.extractor_before_request(request)
    with tempfile.NamedTemporaryFile() as f:
        r = session.send(request, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)
        data = pysolr.Solr(config['solr_url']).extract(f, extractFormat='text')
    data['metadata']['fulltext'] = data['contents']
    return dict(clean_metadatum(*x) for x in data['metadata'].iteritems())


def clean_metadatum(key, value):
    """
    Clean an extracted metadatum.

    Takes a key/value pair and returns it in cleaned form.
    """
    if isinstance(value, list) and len(value) == 1:
        # Flatten 1-element lists
        value = value[0]
    key = key.lower().replace('_', '-')
    return key, value

