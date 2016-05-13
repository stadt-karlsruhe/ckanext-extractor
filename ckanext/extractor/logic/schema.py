#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from inspect import getmembers
import logging

from ckan.lib.navl.validators import ignore_missing, not_empty
from ckan.logic.schema import default_pagination_schema
from ckan.logic.validators import boolean_validator


log = logging.getLogger(__name__)


class _Schema(object):
    """
    Pseudo-class for composable schema definitions.

    Creating an instance of this class will return a dict with the
    class' variables instead of a real instance. This allows you to
    define composable schemas via inheritance::

        class Schema1(_Schema):
            field1 = [not_empty, unicode]

        class Schema2(Schema1):
            field2 = [ignore_missing, unicode]

        print(Schema2())
        # {
        #   'field1': [not_empty, unicode],
        #   'field2': [ignore_missing, unicode]
        # }
    """
    def __new__(cls):
        return {key: value for key, value in getmembers(cls) if not
                key.startswith('__')}


class _MandatoryID(_Schema):
    id = [not_empty, unicode]

extractor_delete = _MandatoryID

class extractor_extract(_MandatoryID):
    force = [ignore_missing, boolean_validator]

extractor_list = default_pagination_schema
extractor_show = _MandatoryID

