#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from ckan.lib.celery_app import celery

from .lib import extract_metadata


@celery.task(name='extractor.update_resource_metadata')
def update_resource_metadata(resource, solr_url):
    print('Update metadata for ' + resource['id'])
    data = extract_metadata(resource['url'], solr_url)
    print('Full text: {}'.format(data['contents']))


@celery.task(name='extractor.delete_resource_metadata')
def delete_resource_metadata(resource):
    print('Delete metadata for ' + resource['id'])

