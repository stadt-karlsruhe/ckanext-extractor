#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

from sqlalchemy import Column, ForeignKey, Table, types

from ckan.model.domain_object import DomainObject
from ckan.model.meta import mapper, metadata
from ckan import model


log = logging.getLogger(__name__)


# What data do we need to store?
#
# - The metadata itself. Each metadata-set is linked to a resource. Since the
#   extracted metadata-fields vary from one filetype to another we should
#   probably use a flexible approach here, e.g. a separate row for each
#   metadata-attribute (id, resource id, attribute name, attribute value). Not
#   sure how one models something like that in SQLAlchemy.
#
# - Metadata about the metadata extraction process. For each resource things
#   like the task ID (if there's an ongoing extraction task), the hashsum of
#   the file, HTTP cache information, etc. This is probably a fixed set of
#   columns, so one row per resource would be OK.


resource_metadatum_table = None
RESOURCE_METADATUM_TABLE_NAME = 'ckanext_extractor_resource_metadatum'


def setup():
    """
    Set up database structure.
    """
    # Gets called from ckanext.extractor.plugin.ExtractorPlugin.configure
    log.debug('setup')
    _setup_resource_metadatum_table()


def _setup_resource_metadatum_table():
    global resource_metadatum_table

    if resource_metadatum_table is None:
        log.debug('Defining resource_metadatum table')
        resource_metadatum_table = Table(
            RESOURCE_METADATUM_TABLE_NAME,
            metadata,
            Column('resource_id', types.UnicodeText, ForeignKey('resource.id',
                   ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                   primary_key=True),
            Column('key', types.UnicodeText, nullable=False),
            Column('value', types.UnicodeText)
        )
        mapper(ResourceMetadatum, resource_metadatum_table)

    if not resource_metadatum_table.exists():
        log.debug('Creating resource_metadatum table')
        resource_metadatum_table.create()
    else:
        log.debug('resource_metadatum table already exists')


class ResourceMetadatum(DomainObject):
    """
    A single resource metadatum (e.g. `fulltext`) and its value.
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

    def update(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
        self.save()

