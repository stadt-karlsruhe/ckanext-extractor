#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import uuid
import tempfile

import pysolr
import requests


def send_task(name, *args):
    """
    Helper for sending a Celery task.

    ``name`` is the name of the task to send. If the name doesn't
    contain a ``.`` then it is prefixed with ``extractor.``.

    Any remaining arguments are passed to the task.
    """
    # Late import at call time because it requires a running app
    from ckan.lib.celery_app import celery
    if '.' not in name:
        name = 'extractor.' + name
    return celery.send_task(name, args, task_id=str(uuid.uuid4()))


def extract_metadata(document_url, solr_url):
    """
    Extract Metadata from content available at an URL.
    """
    with tempfile.NamedTemporaryFile() as f:
        print('Created temporary file {}'.format(f.name))
        r = requests.get(document_url, stream=True)
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)
        print('Finished download from {}'.format(document_url))
        print('Uploading to {} for metadata extraction'.format(solr_url))
        return pysolr.Solr(solr_url).extract(f, extractFormat='text')

