#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit
from ckan.logic import validate
from pylons import config
from sqlalchemy.orm.exc import NoResultFound

from . import schema
from .helpers import check_access, send_task
from ..model import ResourceMetadata, ResourceMetadatum


log = logging.getLogger(__name__)


def _get_metadata(resource_id):
    try:
        return ResourceMetadata.one(resource_id=resource_id)
    except NoResultFound:
        raise toolkit.ObjectNotFound(
            "No metadata found for resource '{}'.".format(resource_id))


@check_access('ckanext_extractor_metadata_delete')
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


@check_access('ckanext_extractor_metadata_extract')
@validate(schema.metadata_extract)
def metadata_extract(context, data_dict):
    """
    Extract and store metadata for a resource.

    Metadata extraction is done in an asynchronous background job, so
    this function may return before extraction is complete.

    :param string id: The ID or name of the resource

    :rtype: A dict with the following keys:

        :task_id: The ID of the background task
    """
    log.debug('metadata_extract')
    res_dict = toolkit.get_action('resource_show')(context, data_dict)
    result = send_task('metadata_extract', config['__file__'], res_dict,
                       config['solr_url'])
    return {'task_id': result.task_id}


@toolkit.side_effect_free
@check_access('ckanext_extractor_metadata_list')
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
@check_access('ckanext_extractor_metadata_show')
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

