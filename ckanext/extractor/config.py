#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from fnmatch import fnmatch

from pylons import config

from ckan.plugins import toolkit


def index_fields():
    """
    Value of the ``ckan.extractor.index_fields`` configuration option.

    :rtype: list
    """
    return [f.lower() for f in
            toolkit.aslist(config.get('ckan.extractor.index_fields', []))]


def index_formats():
    """
    Value of the ``ckan.extractor.index_formats`` configuration option.

    :rtype: list
    """
    return [f.lower() for f in
            toolkit.aslist(config.get('ckan.extractor.index_formats', []))]


def _any_match(s, patterns):
    """
    Check if a string matches at least one pattern.
    """
    for pattern in patterns:
        if fnmatch(s, pattern):
            return True
    return False


def is_field_indexed(name):
    """
    Check if a metadata field is configured to be indexed.
    """
    return _any_match(name.lower(), index_fields())


def is_format_indexed(name):
    """
    Check if a resource format is configured to be indexed.
    """
    return _any_match(name.lower(), index_formats())

