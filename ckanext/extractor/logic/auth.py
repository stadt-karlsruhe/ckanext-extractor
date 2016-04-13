#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


def metadata_delete(context, data_dict):
    """
    Only sysadmins can delete metadata.
    """
    return {'success': False}


def metadata_extract(context, data_dict):
    """
    Only sysadmins can extract metadata.
    """
    return {'success': False}


@toolkit.auth_allow_anonymous_access
def metadata_list(context, data_dict):
    """
    All users can read the list of resources with metadata.
    """
    return {'success': True}


@toolkit.auth_allow_anonymous_access
def metadata_show(context, data_dict):
    """
    All users can read metadata.
    """
    return {'success': True}

