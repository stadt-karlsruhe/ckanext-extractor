#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import collections
import json
import logging

from ckan import plugins
from ckan.logic import NotFound
from ckan.plugins import toolkit

from .config import is_field_indexed, is_format_indexed
from .logic import action, auth
from . import model


log = logging.getLogger(__name__)
get_action = toolkit.get_action


# Template for the Solr field names
SOLR_FIELD = 'ckanext-extractor_{id}_{key}'


def _is_resource(obj):
    """
    Check if a dict describes a resource.

    This is a very simple, duck-typing style test that only checks
    whether the dict contains an ``package_id`` entry.
    """
    return 'package_id' in obj


class ExtractorPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurable)

    #
    # IConfigurer
    #

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'extractor')

    #
    # IConfigurable
    #

    def configure(self, config):
        model.setup()

    #
    # IPackageController / IResourceController
    #

    def after_create(self, context, obj):
        if _is_resource(obj):
            ctx = dict(context, ignore_auth=True)
            get_action('extractor_extract')(ctx, obj)

    def after_update(self, context, obj):
        if _is_resource(obj):
            ctx = dict(context, ignore_auth=True)
            get_action('extractor_extract')(ctx, obj)

    #
    # IResourceController
    #

    def before_delete(self, context, res_dict, res_dicts):
        ctx = dict(context, ignore_auth=True)
        try:
            get_action('extractor_delete')(ctx, res_dict)
        except NotFound:
            # Resource didn't have any metadata
            pass

    #
    # IPackageController
    #

    def before_index(self, pkg_dict):
        data_dict = json.loads(pkg_dict['data_dict'])
        for resource in data_dict['resources']:
            if not is_format_indexed(resource['format']):
                continue
            try:
                metadata = get_action('extractor_show')({}, resource)
            except NotFound:
                continue
            for key, value in metadata['meta'].iteritems():
                if is_field_indexed(key):
                    field = SOLR_FIELD.format(id=resource['id'], key=key)
                    pkg_dict[field] = value
        return pkg_dict

    #
    # IActions
    #

    def get_actions(self):
        return {
            'extractor_delete': action.extractor_delete,
            'extractor_extract': action.extractor_extract,
            'extractor_list': action.extractor_list,
            'extractor_show': action.extractor_show,
        }

    #
    # IAuthFunctions
    #

    def get_auth_functions(self):
        return {
            'extractor_delete': auth.extractor_delete,
            'extractor_extract': auth.extractor_extract,
            'extractor_list': auth.extractor_list,
            'extractor_show': auth.extractor_show,
        }


def task_imports():
    """
    Entry point for Celery task list.
    """
    return ['ckanext.extractor.tasks']

