#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 Stadt Karlsruhe (www.karlsruhe.de)
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

import datetime
import logging
import tempfile

from sqlalchemy.orm.exc import NoResultFound
from requests.exceptions import RequestException

from ckan.lib.search import index_for
from ckan.lib.celery_app import celery
from ckan.plugins import PluginImplementations, toolkit

from .config import is_field_indexed, load_config
from .model import ResourceMetadata, ResourceMetadatum
from .lib import download_and_extract
from .interfaces import IExtractorPostprocessor


log = logging.getLogger(__name__)


@celery.task(name='extractor.extract')
def extract(ini_path, res_dict):
    """
    Download resource, extract and store metadata.

    The extracted metadata is stored in the database.

    Note that this task does check whether the resource exists in the
    database, whether the resource's format is indexed or whether there
    is an existing task working on the resource's metadata. This is the
    responsibility of the caller.

    The task does check which metadata fields are configured to be
    indexed and only stores those in the database.

    Any previously stored metadata for the resource is cleared.
    """
    load_config(ini_path)
    try:
        metadata = ResourceMetadata.one(resource_id=res_dict['id'])
    except NoResultFound:
        metadata = ResourceMetadata.create(resource_id=res_dict['id'])
    try:
        metadata.last_url = res_dict['url']
        metadata.last_format = res_dict['format']
        metadata.last_extracted = datetime.datetime.now()
        metadata.meta.clear()
        extracted = download_and_extract(res_dict['url'])
        for plugin in PluginImplementations(IExtractorPostprocessor):
            plugin.extractor_after_extract(res_dict, extracted)
        for key, value in extracted.iteritems():
            if is_field_indexed(key):
                metadata.meta[key] = value
    except RequestException as e:
        log.warn('Failed to download resource data from "{}": {}'.format(
                 res_dict['url'], e.message))
    finally:
        metadata.task_id = None
        metadata.save()

    for plugin in PluginImplementations(IExtractorPostprocessor):
        plugin.extractor_after_save(res_dict, metadata.as_dict())

    # We need to update the search index for the package here. Note that
    # we cannot rely on the automatic update that happens when a resource
    # is changed, since our extraction task runs asynchronously and may
    # be finished only when the automatic index update has already run.
    pkg_dict = toolkit.get_action('package_show')(
            {'validate': False}, {'id': res_dict['package_id']})
    index_for('package').update_dict(pkg_dict)

    for plugin in PluginImplementations(IExtractorPostprocessor):
        plugin.extractor_after_index(res_dict, metadata.as_dict())

