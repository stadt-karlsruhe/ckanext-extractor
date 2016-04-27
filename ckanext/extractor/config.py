#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from fnmatch import fnmatch
import os.path

import paste.deploy
from pylons import config

from ckan.plugins import toolkit
from ckan.config.environment import load_environment


# Adapted from ckanext-archiver
def load_config(ini_path):
    """
    Load CKAN configuration.
    """
    ini_path = os.path.abspath(ini_path)
    conf = paste.deploy.appconfig('config:' + ini_path)
    load_environment(conf.global_conf, conf.local_conf)


def indexed_fields():
    """
    Value of the ``ckan.extractor.indexed_fields`` configuration option.

    :rtype: list
    """
    fields = config.get('ckanext.extractor.indexed_fields', [])
    return [f.lower() for f in toolkit.aslist(fields)]


def indexed_formats():
    """
    Value of the ``ckan.extractor.indexed_formats`` configuration option.

    :rtype: list
    """
    formats = config.get('ckanext.extractor.indexed_formats', [])
    return [f.lower() for f in toolkit.aslist(formats)]


def _any_match(s, patterns):
    """
    Check if a string matches at least one pattern.
    """
    return any(fnmatch(s, pattern) for pattern in patterns)


def is_field_indexed(field):
    """
    Check if a metadata field is configured to be indexed.
    """
    return _any_match(field.lower(), indexed_fields())


def is_format_indexed(format):
    """
    Check if a resource format is configured to be indexed.
    """
    return _any_match(format.lower(), indexed_formats())

