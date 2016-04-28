#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import tempfile

from ckan.lib.celery_app import celery
from ckan.plugins import toolkit
from sqlalchemy.orm.exc import NoResultFound

from .config import is_field_indexed, load_config
from .model import ResourceMetadata, ResourceMetadatum
from .lib import download_and_extract


@celery.task(name='extractor.metadata_extract')
def metadata_extract(ini_path, res_dict):
    """
    Download resource, extract and store metadata.

    The extracted metadata is stored in the database.

    Note that this task does check whether the resource exists in the
    database, whether the resource's format is indexed or whether there
    is an existing task working on the resource's metadata. This is the
    responsibility of the caller.

    The task does check which metadata fields are configured to be
    indexed and only stores those in the database.

    Any previously stored metadata for the resource is cleared.
    """
    load_config(ini_path)
    try:
        metadata = ResourceMetadata.one(resource_id=res_dict['id'])
    except NoResultFound:
        metadata = ResourceMetadata.create(resource_id=res_dict['id'])
    extracted = download_and_extract(res_dict['url'])
    metadata.meta.clear()
    for key, value in extracted.iteritems():
        if is_field_indexed(key):
            metadata.meta[key] = value
    metadata.last_url = res_dict['url']
    metadata.last_format = res_dict['format']
    metadata.last_extracted = datetime.datetime.now()
    metadata.task_id = None
    metadata.save()

