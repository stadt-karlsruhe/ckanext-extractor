#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

from ckan.plugins import toolkit
from ckan.logic import validate

from ..helpers import check_access
from .. import schema

log = logging.getLogger(__name__)


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
    return {}


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
    return []

