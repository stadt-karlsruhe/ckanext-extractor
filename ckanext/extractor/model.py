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


"""
Data model.

The metadata fields extracted by Solr/Tika vary from one filetype to
another. Therefore a flexible way of storing a resource's metadata is
required instead of a fixed set of columns. We achieve this using a
separate table in which we store both the name and the value of each
individual metadatum. Using SQLAlchemy's ``association_proxy`` and
``attribute_mapped_collection`` that table is then accessed in a dict-
like fashion using the ``ResourceMetadata`` class. This means that you
will probably never need to use the ``ResourceMetadatum`` class.

In addition to the resource metadata, the class ``ResourceMetadata``
also stores information about the extraction process.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging

from sqlalchemy import Column, ForeignKey, Table, types
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from ckan.model.domain_object import DomainObject
from ckan.model.meta import mapper, metadata


log = logging.getLogger(__name__)

resource_metadatum_table = None
RESOURCE_METADATUM_TABLE_NAME = 'ckanext_extractor_resource_metadatum'

resource_metadata_table = None
RESOURCE_METADATA_TABLE_NAME = 'ckanext_extractor_resource_metadata'


class BaseObject(DomainObject):
    """
    Base class for data models.
    """
    @classmethod
    def filter_by(cls, **kwargs):
        return cls.Session.query(cls).filter_by(**kwargs)

    @classmethod
    def one(cls, **kwargs):
        return cls.filter_by(**kwargs).one()

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        cls.Session.add(instance)
        cls.Session.commit()
        return instance

    def delete(self):
        super(BaseObject, self).delete()
        return self


# Gets called from ckanext.extractor.plugin.ExtractorPlugin.configure
def setup():
    """
    Set up database structure.
    """
    log.debug('setup')
    _setup_resource_metadata_table()
    _setup_resource_metadatum_table()


def _setup_resource_metadatum_table():
    global resource_metadatum_table
    if resource_metadatum_table is None:
        log.debug('Defining resource_metadatum table')
        resource_metadatum_table = Table(
            RESOURCE_METADATUM_TABLE_NAME,
            metadata,
            Column('id', types.Integer, nullable=False, primary_key=True),
            Column('resource_id', types.UnicodeText, ForeignKey(
                   RESOURCE_METADATA_TABLE_NAME + '.resource_id',
                   ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            Column('key', types.UnicodeText, nullable=False),
            Column('value', types.UnicodeText)
        )
        mapper(ResourceMetadatum, resource_metadatum_table)
    if not resource_metadatum_table.exists():
        log.debug('Creating resource_metadatum table')
        resource_metadatum_table.create()
    else:
        log.debug('resource_metadatum table already exists')


class ResourceMetadatum(BaseObject):
    """
    A single metadatum of a resource (e.g. ``fulltext``) and its value.
    """
    def __init__(self, key, value=None):
        self.key = key
        self.value = value


def _setup_resource_metadata_table():
    global resource_metadata_table
    if resource_metadata_table is None:
        log.debug('Defining resource_metadata table')
        resource_metadata_table = Table(
            RESOURCE_METADATA_TABLE_NAME,
            metadata,
            Column('resource_id', types.UnicodeText, ForeignKey('resource.id',
                   ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                   primary_key=True),
            Column('last_extracted', types.DateTime),
            Column('last_url', types.UnicodeText),
            Column('last_format', types.UnicodeText),
            Column('task_id', types.UnicodeText)
        )
        mapper(
            ResourceMetadata,
            resource_metadata_table,
            properties={
                '_meta': relationship(ResourceMetadatum, collection_class=
                                      attribute_mapped_collection('key'),
                                      cascade='all, delete, delete-orphan'),
            }
        )
    if not resource_metadata_table.exists():
        log.debug('Creating resource_metadata table')
        resource_metadata_table.create()
    else:
        log.debug('resource_metadate table already exists')


class ResourceMetadata(BaseObject):
    """
    A resource's metadata and information about their extraction.
    """
    meta = association_proxy('_meta', 'value')

