#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging
import uuid

import ckan.plugins.toolkit as toolkit
from ckan.logic import validate
from pylons import config
from sqlalchemy.orm.exc import NoResultFound

from . import schema
from .helpers import check_access
from ..model import ResourceMetadata, ResourceMetadatum
from ..config import is_format_indexed


log = logging.getLogger(__name__)


def _get_metadata(resource_id):
    try:
        return ResourceMetadata.one(resource_id=resource_id)
    except NoResultFound:
        raise toolkit.ObjectNotFound(
            toolkit._("No metadata found for resource '{resource}'.").format(
            resource=resource_id))


@check_access('extractor_metadata_delete')
@validate(schema.metadata_delete)
def metadata_delete(context, data_dict):
    """
    Delete the metadata for a resource.

    :param string id: The ID or the name of the resource
    """
    log.debug('metadata_delete')
    metadata = _get_metadata(data_dict['id'])
    metadata.delete()
    metadata.commit()


@check_access('extractor_metadata_extract')
@validate(schema.metadata_extract)
def metadata_extract(context, data_dict):
    """
    Extract and store metadata for a resource.

    Metadata extraction is done in an asynchronous background job, so
    this function may return before extraction is complete.

    :param string id: The ID or name of the resource

    :rtype: A dict with the following keys:

        :status: A string describing the state of the metadata. This
            can be one of the following:

                :new:  if no metadata for the resource existed before

                :update: if metadata existed but is going to be updated

                :unmodified: if metadata existed but won't get updated
                    (for example because the resource's URL did not
                    change since the last extraction)

                :inprogress: if a background extraction task for this
                    resource is already in progress

                :ignored: if the resource format is configured to be
                    ignored

        :task_id: The ID of the background task. If ``state`` is ``new``
            or ``update`` then this is the ID of a newly created task.
            If ``state`` is ``inprogress`` then it's the ID of the
            existing task. Otherwise it is ``null``.

    """
    log.debug('metadata_extract')
    # Late import at call time because it requires a running app
    from ckan.lib.celery_app import celery
    resource = toolkit.get_action('resource_show')(context, data_dict)
    task_id = None
    try:
        metadata = ResourceMetadata.one(resource_id=resource['id'])
        if metadata.task_id:
            status = 'inprogress'
            task_id = metadata.task_id
        elif not is_format_indexed(resource['format']):
            metadata.delete()
            metadata.commit()
            status = 'ignore'
        elif (metadata.last_url != resource['url']
              or metadata.last_format != resource['format']):
            status = 'update'
        else:
            status = 'unmodified'
    except NoResultFound:
        if is_format_indexed(resource['format']):
            metadata = ResourceMetadata.create(resource_id=resource['id'])
            status = 'new'
        else:
            status = 'ignore'
    if status in ('new', 'update'):
        task_id = metadata.task_id = str(uuid.uuid4())
        metadata.save()
        args = (config['__file__'], resource, config['solr_url'])
        res = celery.send_task('extractor.metadata_extract', args, task_id=task_id)
    return {
        'status': status,
        'task_id': task_id,
    }


@toolkit.side_effect_free
@check_access('extractor_metadata_list')
@validate(schema.metadata_list)
def metadata_list(context, data_dict):
    """
    List the resources for which metadata has been extracted.

    :param int limit: If given, the list of datasets will be broken into
        pages of at most ``limit`` datasets per page and only one page
        will be returned at a time (optional).

    :param int offset: If ``limit`` is given the offset to start
        returning resources from.

    :rtype: List of resource IDs
    """
    log.debug('metadata_list')
    return [m.resource_id for m in ResourceMetadata.all()]


@toolkit.side_effect_free
@check_access('extractor_metadata_show')
@validate(schema.metadata_show)
def metadata_show(context, data_dict):
    """
    Show the stored metadata for a resource.

    :param string id: The ID or name of the resource

    :rtype: dict
    """
    log.debug('metadata_show')
    metadata = _get_metadata(data_dict['id'])
    result = metadata.as_dict()
    result['meta'] = dict(metadata.meta)
    return result

