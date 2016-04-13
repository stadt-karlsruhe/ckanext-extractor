#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


@toolkit.side_effect_free
def metadata_show(context, data_dict):
    """
    Show the stored metadata for a resource.

    :param string id: The ID or name of the resource
    """
    log.debug('metadata_show')
    toolkit.check_access('ckanext_extractor_metadata_show', context, data_dict)
    return {}


@toolkit.side_effect_free
def metadata_list(context, data_dict):
    """
    List the resources for which metadata has been extracted.
    """
    log.debug('metadata_list')
    toolkit.check_access('ckanext_extractor_metadata_list', context, data_dict)
    return []

