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

import logging
import uuid

import ckan.plugins.toolkit as toolkit
from ckan.logic import validate
from pylons import config
from sqlalchemy.orm.exc import NoResultFound

from . import schema
from .helpers import check_access
from ..model import ResourceMetadata, ResourceMetadatum
from ..config import is_format_indexed


log = logging.getLogger(__name__)


def _get_metadata(resource_id):
    try:
        return ResourceMetadata.one(resource_id=resource_id)
    except NoResultFound:
        raise toolkit.ObjectNotFound(
            toolkit._("No metadata found for resource '{resource}'.").format(
            resource=resource_id))


@check_access('extractor_delete')
@validate(schema.extractor_delete)
def extractor_delete(context, data_dict):
    """
    Delete the metadata for a resource.

    :param string id: The ID or the name of the resource
    """
    log.debug('extractor_delete {}'.format(data_dict['id']))
    metadata = _get_metadata(data_dict['id'])
    metadata.delete().commit()


@check_access('extractor_extract')
@validate(schema.extractor_extract)
def extractor_extract(context, data_dict):
    """
    Extract and store metadata for a resource.

    Metadata extraction is done in an asynchronous background job, so
    this function may return before extraction is complete.

    :param string id: The ID or name of the resource

    :param boolean force: Extract metadata even if the resource hasn't
        changed, or if an extraction task is already scheduled for the
        resource (optional).

    :rtype: A dict with the following keys:

        :status: A string describing the state of the metadata. This
            can be one of the following:

                :new: if no metadata for the resource existed before

                :update: if metadata existed but is going to be updated

                :unchanged: if metadata existed but won't get updated
                    (for example because the resource's URL did not
                    change since the last extraction)

                :inprogress: if a background extraction task for this
                    resource is already in progress

                :ignored: if the resource format is configured to be
                    ignored

            Note that if ``force`` is true then an extraction job will
            be scheduled regardless of the status reported, unless that
            status is ``ignored``.

        :task_id: The ID of the background task. If ``state`` is ``new``
            or ``update`` then this is the ID of a newly created task.
            If ``state`` is ``inprogress`` then it's the ID of the
            existing task. Otherwise it is ``null``.

            If ``force`` is true then this is the ID of the new
            extraction task.

    """
    log.debug('extractor_extract {}'.format(data_dict['id']))
    # Late import at call time because it requires a running app
    from ckan.lib.celery_app import celery
    force = data_dict.get('force', False)
    resource = toolkit.get_action('resource_show')(context, data_dict)
    task_id = None
    metadata = None
    try:
        metadata = ResourceMetadata.one(resource_id=resource['id'])
        if metadata.task_id:
            status = 'inprogress'
            task_id = metadata.task_id
        elif not is_format_indexed(resource['format']):
            metadata.delete()
            metadata.commit()
            metadata = None
            status = 'ignored'
        elif (metadata.last_url != resource['url']
              or metadata.last_format != resource['format']):
            status = 'update'
        else:
            status = 'unchanged'
    except NoResultFound:
        if is_format_indexed(resource['format']):
            status = 'new'
        else:
            status = 'ignored'
    if status in ('new', 'update') or (status != 'ignored' and force):
        if metadata is None:
            metadata = ResourceMetadata.create(resource_id=resource['id'])
        task_id = metadata.task_id = str(uuid.uuid4())
        metadata.save()
        args = (config['__file__'], resource)
        celery.send_task('extractor.extract', args, task_id=task_id)
    return {
        'status': status,
        'task_id': task_id,
    }


@toolkit.side_effect_free
@check_access('extractor_list')
@validate(schema.extractor_list)
def extractor_list(context, data_dict):
    """
    List resources that have metadata.

    Returns a list with the IDs of the resources which have metadata
    associated with them.

    :rtype: list
    """
    log.debug('extractor_list')
    return [m.resource_id for m in ResourceMetadata.filter_by(task_id=None)]


@toolkit.side_effect_free
@check_access('extractor_show')
@validate(schema.extractor_show)
def extractor_show(context, data_dict):
    """
    Show the stored metadata for a resource.

    :param string id: The ID or name of the resource

    :rtype: dict
    """
    log.debug('extractor_show {}'.format(data_dict['id']))
    metadata = _get_metadata(data_dict['id'])
    result = metadata.as_dict()
    result['meta'] = dict(metadata.meta)
    return result

