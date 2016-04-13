#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit
from ckan.logic import get_action, validate
from pylons import config

from .helpers import check_access, send_task
from . import schema


log = logging.getLogger(__name__)


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
    res_dict = get_action('resource_show')(context, data_dict)
    result = send_task('metadata_extract', res_dict, config.get('solr_url'))
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

    :rtype: List of strings
    """
    log.debug('metadata_list')
    # FIXME: Implement this
    return []


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
    # FIXME: Implement this
    return {}


@check_access('ckanext_extractor_metadata_delete')
@validate(schema.metadata_delete)
def metadata_delete(context, data_dict):
    """
    Delete the metadata for a resource.

    :param string id: The ID or the name of the resource
    """
    log.debug('metadata_delete')
    # FIXME: Implement this

