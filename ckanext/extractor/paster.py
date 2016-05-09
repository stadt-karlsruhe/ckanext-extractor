#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import sys

from sqlalchemy import inspect

from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit
from ckan.logic import NotFound

from .model import ResourceMetadata


def _error(msg):
    sys.exit('ERROR: ' + msg)


def _compress(s, n=50):
    s = unicode(s)
    if len(s) < n:
        return s
    else:
        return s[:n/2] + ' ... ' + s[-n/2:]


class ExtractorCommand(CkanCommand):
    """
    Base class for ckanext.extractor Paster commands.
    """
    def _get_ids(self, only_with_metadata=False):
        """
        Get list of resource IDs from command line arguments.

        Returns the specific IDs listed or all IDs if ``all`` was passed.

        If ``only_with_metadata`` is true and ``all`` was passed then only
        IDs of resources which have metadata are returned.
        """
        if len(self.args) < 1:
            _error('Missing argument. Specify one or more resource IDs '
                   + 'or "all".')
        if len(self.args) == 1 and self.args[0].lower() == 'all':
            if only_with_metadata:
                context = {'ignore_auth': True}
                return sorted(toolkit.get_action('extractor_metadata_list')(
                              context, {}))
            else:
                from ckan.model import Resource
                return sorted(r.id for r in Resource.active())
        else:
            return self.args[:]


class DeleteCommand(ExtractorCommand):
    """
    Delete metadata

    delete (all | ID [ID [...]])
    """
    max_args = None
    min_args = 1
    usage = __doc__
    summary = __doc__.strip().split('\n')[0]

    def command(self):
        self._load_config()
        delete = toolkit.get_action('extractor_metadata_delete')
        context = {'ignore_auth': True}
        for id in self._get_ids(True):
            print(id)
            delete(context, {'id': id})


class ExtractCommand(ExtractorCommand):
    """
    Extract metadata

    extract [--force] (all | ID [ID [...]])

    If --force is given then extraction is performed even if the
    resource format is ignored, the resource hasn't changed, or
    another extraction task for the resource is already in progress.

    Note that Celery must be running, this command only schedules the
    necessary background tasks.
    """
    max_args = None
    min_args = None
    usage = __doc__
    summary = __doc__.strip().split('\n')[0]

    def __init__(self, name):
        super(ExtractCommand, self).__init__(name)
        self.parser.add_option('--force', default=False,
                               help='Force extraction',
                               action='store_true')

    def command(self):
        self._load_config()
        extract = toolkit.get_action('extractor_metadata_extract')
        context = {'ignore_auth':  True}
        for id in self._get_ids():
            print(id + ': ', end='')
            result = extract(context, {'id': id, 'force': self.options.force})
            status = result['status']
            if result['task_id']:
                status += ' (task {})'.format(result['task_id'])
            print(status)


class ListCommand(ExtractorCommand):
    """
    List resources with metadata
    """
    max_args = 0
    min_args = 0
    usage = __doc__
    summary = __doc__.strip().split('\n')[0]

    def command(self):
        self._load_config()
        context = {'ignore_auth': True}
        result = toolkit.get_action('extractor_metadata_list')(context, {})
        print('\n'.join(sorted(result)))


class ShowCommand(ExtractorCommand):
    """
    Show metadata

    show (all | ID [ID [...]])
    """
    max_args = None
    min_args = 1
    usage = __doc__
    summary = __doc__.strip().split('\n')[0]

    def command(self):
        self._load_config()
        show = toolkit.get_action('extractor_metadata_show')
        context = {'ignore_auth': True}
        ids = self._get_ids(True)
        for i, id in enumerate(ids):
            try:
                result = show(context, {'id': id})
            except NotFound as e:
                print(e)
                continue
            print('{}:'.format(id))
            for key in sorted(result):
                if key in ('resource_id', 'meta'):
                    continue
                print('  {}: {!r}'.format(key, result[key]))
            print('  meta:')
            meta = result['meta']
            for key in sorted(meta):
                print('    {}: {!r}'.format(key, _compress(meta[key])))
            if i < len(ids) - 1:
                print('')


