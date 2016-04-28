#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import tempfile

from pylons import config
import pysolr
import requests


def download_and_extract(resource_url):
    """
    Download resource and extract metadata using Solr.

    The extracted metadata is cleaned and returned.
    """
    with tempfile.NamedTemporaryFile() as f:
        r = requests.get(resource_url, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)
        data = pysolr.Solr(config['solr_url']).extract(f, extractFormat='text')
    data['metadata']['contents'] = data['contents']
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

