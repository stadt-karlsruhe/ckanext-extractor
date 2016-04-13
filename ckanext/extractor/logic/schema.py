#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging

from ckan.lib.navl.validators import not_empty
from ckan.logic.schema import default_pagination_schema


log = logging.getLogger(__name__)


def _mandatory_id():
    log.debug('_mandatory_id')
    return {
        'id': [not_empty, unicode],
    }


metadata_extract = _mandatory_id


def metadata_list():
    return default_pagination_schema()


metadata_show = _mandatory_id

