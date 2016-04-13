#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


@toolkit.auth_allow_anonymous_access
def metadata_show(context, data_dict):
    """
    All users can read metadata.
    """
    return {'success': True}


@toolkit.auth_allow_anonymous_access
def metadata_list(context, data_dict):
    """
    All users can read the list of resources with metadata.
    """
    return {'success': True}

