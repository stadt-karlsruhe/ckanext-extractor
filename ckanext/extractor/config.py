#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016 Stadt Karlsruhe (www.karlsruhe.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import absolute_import, print_function, unicode_literals

from fnmatch import fnmatch
import os.path
from string import lower

import paste.deploy
from paste.registry import Registry
from pylons import config, translator

from ckan.plugins import toolkit
from ckan.config.environment import load_environment
from ckan.lib.cli import MockTranslator


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
    _register_translator()


# Adapted from ckanext-archiver
def _register_translator():
    """
    Register a translator in this thread.
    """
    global registry
    try:
        registry
    except NameError:
        registry = Registry()
    registry.prepare()
    global translator_obj
    try:
        translator_obj
    except NameError:
        translator_obj = MockTranslator()
    registry.register(translator, translator_obj)


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

