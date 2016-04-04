#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import io
import logging
import tempfile

from pylons import config
import pysolr
import requests

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit



log = logging.getLogger(__name__)


def _is_package(obj):
    """
    Check if a dict describes a package.

    This is a very simple, duck-typing style test that only checks
    whether the dict contains an ``owner_org`` entry.
    """
    return 'owner_org' in obj


def _extract(url):
    """
    Extract Metadata from content available at an URL.
    """
    # FIXME: Fulltext is returned as HTML
    with tempfile.NamedTemporaryFile() as f:
        log.debug('Created temporary file {}'.format(f.name))
        r = requests.get(url, stream=True)
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)
        log.debug('Finished download from {}'.format(url))
        solr = pysolr.Solr(config.get('solr_url'))
        return solr.extract(f)


class ExtractorPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'extractor')

    # IPackageController / IResourceController

    def after_create(self, context, obj):
        if _is_package(obj):
            log.debug('A package was created: {}'.format(obj['id']))
        else:
            log.debug('A resource was created: {}'.format(obj['id']))

    def after_update(self, context, obj):
        if _is_package(obj):
            log.debug('A package was updated: {}'.format(obj['id']))
        else:
            log.debug('A resource was updated: {}'.format(obj['id']))
            data = _extract(obj['url'])
            log.debug('Full text: {}'.format(data['contents']))

    def after_delete(self, context, obj):
        if _is_package(obj):
            log.debug('A package was deleted: {}'.format(obj['id']))
        else:
            log.debug('A resource was deleted: {}'.format(obj['id']))

    def before_index(self, pkg_dict):
        log.debug('Package {} will be indexed'.format(pkg_dict['id']))
        return pkg_dict

