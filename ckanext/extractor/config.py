#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from fnmatch import fnmatch
import os.path
from string import lower

import paste.deploy
from pylons import config

from ckan.plugins import toolkit
from ckan.config.environment import load_environment


DEFAULTS = {
    'ckanext.extractor.indexed_formats': 'pdf',
    'ckanext.extractor.indexed_fields': 'contents',
}

TRANSFORMATIONS = {
    'ckanext.extractor.indexed_formats': [lower, toolkit.aslist],
    'ckanext.extractor.indexed_fields': [lower, toolkit.aslist],
}


def get(setting):
    """
    Get configuration setting.

    ``setting`` is the setting without the ``ckanext.extractor.``
    prefix.

    Handles defaults and transformations.
    """
    setting = 'ckanext.extractor.' + setting
    value = config.get(setting, DEFAULTS[setting])
    for transformation in TRANSFORMATIONS[setting]:
        value = transformation(value)
    return value


# Adapted from ckanext-archiver
def load_config(ini_path):
    """
    Load CKAN configuration.
    """
    ini_path = os.path.abspath(ini_path)
    conf = paste.deploy.appconfig('config:' + ini_path)
    load_environment(conf.global_conf, conf.local_conf)


def _any_match(s, patterns):
    """
    Check if a string matches at least one pattern.
    """
    return any(fnmatch(s, pattern) for pattern in patterns)


def is_field_indexed(field):
    """
    Check if a metadata field is configured to be indexed.
    """
    return _any_match(field.lower(), get('indexed_fields'))


def is_format_indexed(format):
    """
    Check if a resource format is configured to be indexed.
    """
    return _any_match(format.lower(), get('indexed_formats'))

