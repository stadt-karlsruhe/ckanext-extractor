#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from ckan.model.resource import resource_table
from sqlalchemy import types, ForeignKey

Base = declarative_base()

class ResourceMetaData(Base):
    pass

