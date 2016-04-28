#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import tempfile

from ckan.lib.celery_app import celery
from ckan.plugins import toolkit
from sqlalchemy.orm.exc import NoResultFound

from .config import is_field_indexed, is_format_indexed, load_config
from .model import ResourceMetadata, ResourceMetadatum
from .lib import download_and_extract


@celery.task(name='extractor.metadata_extract')
def metadata_extract(ini_path, resource):
    load_config(ini_path)
    try:
        metadata = ResourceMetadata.one(resource_id=resource['id'])
    except NoResultFound:
        metadata = ResourceMetadata.create(resource_id=resource['id'])
    extracted = download_and_extract(resource['url'])
    metadata.meta.clear()
    if is_format_indexed(resource['format']):
        for key, value in extracted.iteritems():
            if is_field_indexed(key):
                metadata.meta[key] = value
    metadata.last_url = resource['url']
    metadata.last_format = resource['format']
    metadata.last_extracted = datetime.datetime.now()
    metadata.task_id = None
    metadata.save()

