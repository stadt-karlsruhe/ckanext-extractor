#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit
from ckan.logic import validate

from ..helpers import check_access
from .. import schema


log = logging.getLogger(__name__)


@check_access('ckanext_extractor_metadata_extract')
@validate(schema.metadata_extract)
def metadata_extract(context, data_dict):
    """
    Extract and store metadata for a resource.

    :param string id: The ID or name of the resource
    """
    log.debug('metadata_extract')
    return {}

