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

from ckan import plugins


class IExtractorPostprocessor(plugins.Interface):
    '''
    Postprocess extracted metadata.

    This interfaces provides hooks for postprocess resource metadata
    after its extraction. They can be used to modify the metadata before
    it is stored or to automatically trigger actions that use the
    extraction results for other purposes.

    Note that none of the hooks are called if an exception ocurred
    during the extraction.
    '''
    def extractor_after_extract(self, resource_dict, extracted):
        '''
        Postprocess metadata after extraction.

        Called directly after metadata has been extracted and
        normalized. ``extracted`` is a dict containing the metadata.

        Implementations can modify ``extracted`` in place, the return
        value of the function is ignored.

        Note that filtering of metadata according to
        ``ckanext.extractor.indexed_fields`` is done after this function
        is called.
        '''

    def extractor_after_save(self, resource_dict, metadata_dict):
        '''
        Postprocess metadata after it has been saved.

        Called after metadata has been extracted and saved in the
        database.

        ``metadata_dict`` is a dict-representation of the resource's
        ``ckanext.extractor.model.ResourceMetadata`` instance. Changes
        to ``metadata_dict`` and the return value of the function are
        ignored.

        Note: When this function is called the fields have been filtered
        according to ``ckanext.extractor.indexed_fields``, but the
        extracted metadata hasn't been indexed, yet.
        '''

    def extractor_after_index(self, resource_dict, metadata_dict):
        '''
        Postprocess metadata after it has been indexed.

        Called after the package of the resource whose metadata has been
        extracted has been re-indexed after the extraction.

        ``resource_dict`` and ``metadata_dict`` are dict-representations
        of the resource and the metadata, respectively. Changes to them
        and the return value of the function are ignored.

        Note: When this function is called the fields have been filtered
        according to ``ckanext.extractor.indexed_fields``.
        '''


class IExtractorRequest(plugins.Interface):
    '''
    Alter HTTP download requests.

    This interface allows you to modify the HTTP request for downloading
    a resource file, e.g. if the remote server requires certain
    authentication headers.
    '''
    def extractor_before_request(self, request):
        '''
        Alter a HTTP download request.

        ``request`` is a ``PreparedRequest`` object.

        This function must return a ``PreparedRequest`` object, which
        can either be the original request after it has been modified or
        a completely new one.

        Details can be found in the `requests documentation
        <http://docs.python-requests.org/en/master/user/advanced/>`_.
        '''
        return request
