#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from pprint import pprint

from ckan.lib.celery_app import celery

from .lib import extract_metadata


@celery.task(name='extractor.update_resource_metadata')
def update_resource_metadata(resource, solr_url):
    # 1. Check if we already have metadata for that resource ID
    # 2. Download resource. Here we should make use of HTTP caching features
    #    to avoid reprocessing existing data: For example, if a resource's
    #    description changed we don't need to do the whole process again.
    #    In addition to the HTTP cache metadata we should also store the file
    #    hash.
    # 3. If the resource changed then re-extract the metadata.
    # 4. Update the information in the database.
    print('Update metadata for ' + resource['id'])
    data = extract_metadata(resource['url'], solr_url)
    #print('Full text: {}'.format(data['contents']))
    pprint(data)
    # Do we need to trigger a re-indexing of the package at this point?


@celery.task(name='extractor.delete_resource_metadata')
def delete_resource_metadata(resource):
    print('Delete metadata for ' + resource['id'])

