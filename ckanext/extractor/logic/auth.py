#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


def _only_sysadmins(context, datadict):
    return {'success': False}


@toolkit.auth_allow_anonymous_access
def _everybody(context, datadict):
    return {'success': True}


metadata_delete = _only_sysadmins
metadata_extract = _only_sysadmins
metadata_list = _everybody
metadata_show = _everybody

