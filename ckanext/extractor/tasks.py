#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import tempfile

import pysolr
import requests

from ckan.lib.celery_app import celery


@celery.task(name='ckanext_extractor_metadata_extract')
def metadata_extract(resource, solr_url):
    # 1. Check if we already have metadata for that resource ID
    # 2. Download resource. Here we should make use of HTTP caching features
    #    to avoid reprocessing existing data: For example, if a resource's
    #    description changed we don't need to do the whole process again.
    #    In addition to the HTTP cache metadata we should also store the file
    #    hash.
    # 3. If the resource changed then re-extract the metadata.
    # 4. Update the information in the database.
    print('Extract metadata for ' + resource['id'])
    with tempfile.NamedTemporaryFile() as f:
        print('Created temporary file {}'.format(f.name))
        r = requests.get(resource['url'], stream=True)
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)
        print('Finished download from {}'.format(resource['url']))
        print('Uploading to {} for metadata extraction'.format(solr_url))
        data = pysolr.Solr(solr_url).extract(f, extractFormat='text')
    print('Finished extracting metadata from {}'.format(resource['url']))
    #print('Full text: {}'.format(data['contents']))
    # Do we need to trigger a re-indexing of the package at this point?

