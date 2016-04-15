#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os.path
import tempfile

import pysolr
import requests

from ckan.config.environment import load_environment
from ckan.lib.celery_app import celery
from ckan.plugins import toolkit
import paste.deploy
from sqlalchemy.orm.exc import NoResultFound

from .model import ResourceMetadata, ResourceMetadatum


@celery.task(name='ckanext_extractor.metadata_extract')
def metadata_extract(ini_path, resource, solr_url):
    # FIXME: To avoid re-extracting existing metadata it is probably enough to
    # check whether the resource URL has changed.
    print('Loading config')
    _load_config(ini_path)
    print('Extract metadata for ' + resource['id'])
    data = _download_and_extract(resource['url'], solr_url)
    try:
        metadata = ResourceMetadata.one(resource_id=resource['id'])
        print('Replaced existing metadata')
    except NoResultFound:
        metadata = ResourceMetadata.create(resource_id=resource['id'])
        print('Created new metadata')
    print('Setting contents')
    metadata.meta.clear()
    metadata.meta['contents'] = data['contents']
    for key, value in data['metadata'].iteritems():
        key, value = _clean(key, value)
        print('{!r} = {!r}'.format(key, value))
        metadata.meta[key] = value
    print('Saving changes')
    metadata.save()


# Adapted from ckanext-archiver
def _load_config(ini_path):
    ini_path = os.path.abspath(ini_path)
    conf = paste.deploy.appconfig('config:' + ini_path)
    load_environment(conf.global_conf, conf.local_conf)


def _clean(key, value):
    """
    Clean an extracted metadatum.

    Takes a key/value pair and returns it in cleaned form.
    """
    # Flatten 1-element lists
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    key = key.lower().replace('_', '-')
    return key, value


def _download_and_extract(resource_url, solr_url):
    """
    Download resource and extract metadata using Solr.

    The extracted metadata is returned.
    """
    with tempfile.NamedTemporaryFile() as f:
        print('Created temporary file {}'.format(f.name))
        r = requests.get(resource_url, stream=True)
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)
        print('Finished download from {}'.format(resource_url))
        print('Uploading to {} for metadata extraction'.format(solr_url))
        return pysolr.Solr(solr_url).extract(f, extractFormat='text')
        print('Finished extracting metadata from {}'.format(resource_url))

