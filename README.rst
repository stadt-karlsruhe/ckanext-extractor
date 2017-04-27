ckanext-extractor
#################

.. image:: https://travis-ci.org/stadt-karlsruhe/ckanext-extractor.svg?branch=master
    :target: https://travis-ci.org/stadt-karlsruhe/ckanext-extractor

A CKAN_ extension for automatically extracting text and metadata from datasets.

*ckanext-extractor* automatically extracts text and metadata from your
resources and adds them to the search index so that they can be used to find
your data.

.. _CKAN: https://www.ckan.org


Requirements
============
*ckanext-extractor* has been developed and tested with CKAN 2.5.2. Other
versions may or may not work, please share your experiences by `creating an
issue`_.

.. _creating an issue: https://github.com/stadt-karlsruhe/ckanext-extractor/issues


Installation
============
**Note:** The following steps assume a standard CKAN source installation.

Install Python Package
----------------------
Activate your CKAN virtualenv::

    . /usr/lib/ckan/default/bin/activate

Install the latest development version of *ckanext-extractor* and its
dependencies::

    cd /usr/lib/ckan/default
    pip install -e git+https://github.com/stadt-karlsruhe/ckanext-extractor#egg=ckanext-extractor
    pip install -r src/ckanext-extractor/requirements.txt

On a production system you'll probably want to pin a certain `release version`_
of *ckanext-extractor* instead::

    pip install -e git+https://github.com/stadt-karlsruhe/ckanext-extractor@v0.2.0#egg=ckanext-extractor

.. _release version: https://github.com/stadt-karlsruhe/ckanext-extractor/releases

Configure CKAN
--------------
Open your CKAN configuration file (e.g. ``/etc/ckan/default/production.ini``)
and add ``extractor`` to the list of plugins::

    ckan.plugins = ... extractor

Initialize the database::

    paster --plugin=ckanext-extractor init -c /etc/ckan/default/production.ini


Start Celery Daemon
-------------------
*ckanext-extractor* uses Celery background tasks to perform the extraction
asynchronously so that they do not block the web server. You therefore need to
make sure that Celery is running, for example using

::

    paster --plugin=ckan celeryd -c /etc/ckan/default/production.ini

See the `CKAN documentation`_ for more information on Celery.


.. _`CKAN documentation`: http://docs.ckan.org/en/latest/maintaining/background-tasks.html


Configure Solr
--------------
For the actual extraction CKAN's Apache Solr server is used. However, the
necessary Solr plugins are deactivated by default. To enable them, find your
main Solr configuration file (usually ``/etc/solr/conf/solrconfig.xml``) and
add/uncomment the following lines::

    <lib dir="../../dist/" regex="apache-solr-cell-\d.*\.jar" />
    <lib dir="../../contrib/extraction/lib" regex=".*\.jar" />

**Note:** The Solr packages on Ubuntu are broken_ and do not contain the
necessary files. You can simply download an `official release`_ of the same
version, unpack it to a suitable location (without installing it) and adjust
the ``dir`` arguments in the configuration lines above accordingly. For
example, if you have unpacked the files to ``/var/lib/apache-solr``, then you
would need to put the following lines into ``solrconfig.xml``::

    <lib dir="/var/lib/apache-solr/dist/" regex="apache-solr-cell-\d.*\.jar" />
    <lib dir="/var/lib/apache-solr/contrib/extraction/lib" regex=".*\.jar" />

.. _broken: https://bugs.launchpad.net/ubuntu/+source/lucene-solr/+bug/1565637
.. _`official release`: http://archive.apache.org/dist/lucene/solr

Once the text and metadata have been extracted they need to be added to the
Solr index, which requires appropriate Solr fields. To set them up add the
following lines to your Solr schema configuration (usually
``/etc/solr/conf/schema.xml``)::

    # Directly before the line that says "</fields>"
    <dynamicField name="ckanext-extractor_*" type="text" indexed="true" stored="false"/>

    # Directly before the line that says "</schema>"
    <copyField source="ckanext-extractor_*" dest="text"/>

Make sure to restart Solr after you have applied the changes. For example, if
you're using Jetty as an application server for Solr, then

::

    sudo service jetty restart


Restart CKAN
------------
Finally, restart your CKAN server::

    sudo service apache2 restart


Test your Installation
----------------------
The installation is now complete. To verify that everything is working open the
URL ``/api/3/action/extractor_list``, e.g. via

::

    wget -qO - http://localhost/api/3/action/extractor_list

The output should look like this (in particular, ``success`` should ``true``)::

    {"help": "http://localhost/api/3/action/help_show?name=extractor_list", "success": true, "result": []}


You're Done!
------------
Your installation of *ckanext-extractor* is now complete, and new/updated
resources will have their metadata automatically indexed. You may want to
adapt the configuration to your needs, see below for details. Once that is
done you may also want to extract metadata from your existing resources::

    . /usr/lib/ckan/default/bin/activate
    paster --plugin=ckanext-extractor extract all -c /etc/ckan/default/production.ini

This and other ``paster`` administration commands are explained below in more
detail.


Configuration
=============
*ckanext-extractor* can be configured via the usual CKAN configuration file (e.g.
``/etc/ckan/default/production.ini``). You must restart your CKAN server after
updating the configuration.

Formats for Extraction
----------------------
While Solr can extract text and metadata from many file formats not all of
them might be of interest to you. You can therefore configure for which formats
extraction is performed via the ``ckanext.extractor.indexed_formats`` option. It
takes a list of space-separated formats, where the format is the one specified
in a resource's CKAN metadata (and not the file extension or MIME type)::

    ckanext.extractor.indexed_formats = pdf txt

Formats are case-insensitive. You can use wildcards (``*`` and ``?``) to match
multiple formats. To extract data from all formats simply set

::

    ckanext.extractor.indexed_formats = *

By default, extraction is only enabled for the PDF format::

    ckanext.extractor.indexed_formats = pdf

Fields for Indexing
-------------------
Once text and metadata have been extracted they can be added to the search
index. Again, Solr supports more metadata fields than one usually needs. You
can therefore configure which fields are indexed via the
``ckanext.extractor.indexed_fields`` option. It takes a space-separated list of
field names::

    ckanext.extractor.indexed_fields = fulltext author

The full text of a document is available via the ``fulltext`` field. Field names
are case-insensitive. You can use wildcards (``*`` and ``?``) to match multiple
field names. To index all fields simply set

::

    ckanext.extractor.indexed_fields = *

By default, only the full text of a document is indexed::

    ckanext.extractor.indexed_fields = fulltext

**Note:** *ckanext-extractor* normalizes the field names reported by Solr by
replacing underscores (``_``) with hyphens (``-``).


Paster Commands
===============
In general, *ckanext-extractor* works automatically: whenever a new resource is
created or an existing resource changes, its metadata is extracted and indexed.
However, for administration purposes, metadata can also be managed from the
command line using the paster_ tool.

.. _paster: http://docs.ckan.org/en/latest/maintaining/paster.html

**Note:** You have to activate your virtualenv before you can use these
commands::

    . /usr/lib/ckan/default/bin/activate

The general form for a paster command is

::

    paster --plugin=ckanext-extractor COMMAND ARGUMENTS --config=/etc/ckan/default/production.ini

Replace ``COMMAND`` and ``ARGUMENTS`` as described below. For example::

    paster --plugin=ckanext-extractor extract all --config=/etc/ckan/default/production.ini


- ``delete (all | ID [ID [...]])``: Delete metadata. You can specify one or
  more resource IDs or a single ``all`` argument (in which case all metadata is
  deleted).

- ``extract [--force] (all | ID [ID [...]])``: Extract metadata. You can
  specify one or more resource IDs or a single ``all`` argument (in which case
  metadata is extracted from all resources with appropriate formats). An
  optional ``--force`` argument can be used to force extraction even if the
  resource is unchanged, or if another extraction job already has been
  scheduled for that resource.

  Note that this command only schedules the necessary extraction background
  tasks. The Celery daemon has to be running for the extraction to actually
  happen.

- ``init``: Initialize the database tables for *ckanext-extractor*. You only
  need to use this once (during the installation).

- ``list``: List the IDs of all resources for which metadata has been
  extracted.

- ``show (all | ID [ID [...]])``: Show extracted metadata. You can specify one
  or more resource IDs or a single ``all`` argument (in which case all metadata
  is shown).


API
===
Metadata can be managed via the standard `CKAN API`_. Unless noted otherwise
all commands are only available via POST requests to authenticated users.

.. _`CKAN API`: http://docs.ckan.org/en/latest/api/index.html

``extractor_delete``
--------------------
Delete metadata.

Only available to administrators.

Parameters:

:id: ID of the resource for which metadata should be deleted.


``extractor_extract``
---------------------
Extract metadata.

This function schedules a background task for extracting metadata from a
resource.

Only available to administrators.

Parameters:

:id: ID of the resource for which metadata should be extracted.

:force: Optional boolean flag to force extraction even if the resource is
    unchanged, or if an extraction task has already been scheduled for that
    resource.

Returns a dict with the following entries:

:status: A string describing the state of the metadata. This can be one of the
    following:

    :new: if no metadata for the resource existed before

    :update: if metadata existed but is going to be updated

    :unchanged: if metadata existed but won't get updated (for example because
        the resource's URL did not change since the last extraction)

    :inprogress: if a background extraction task for this resource is already
        in progress

    :ignored: if the resource format is configured to be ignored

    Note that if ``force`` is true then an extraction job will be scheduled
    regardless of the status reported, unless that state is ``ignored``.

:task_id: The ID of the background task. If ``state`` is ``new`` or ``update``
    then this is the ID of a newly created task. If ``state`` is ``inprogress``
    then it's the ID of the existing task. Otherwise it is ``null``.

    If ``force`` is true then this is the ID of the new extraction task.

``extractor_list``
------------------
List resources with metadata.

Returns a list with the IDs of all resources for which metadata has been
extracted.

Available to all (even anonymous) users via GET and POST.

``extractor_show``
------------------
Show the metadata for a resource.

Parameters:

:id: ID of the resource for which metadata should be extracted.

Returns a dict with the resource's metadata and information about the last
extraction.

Available to all (even anonymous) users via GET and POST.


Postprocessing Extraction Results
=================================
The ``ckanext.extractor.interfaces.IExtractorPostprocessor`` interface can be
used to hook into the extraction process. It allows you to postprocess
extraction results and to automatically trigger actions that use the extraction
results for other purposes.

The interface offers 3 hooks:

- ``extractor_after_extract(resource_dict, extracted)`` is called right after
  the extraction before the extracted metadata ``extracted`` is filtered and
  stored. You can modify ``extracted`` (in-place) and the changes will end up
  in the database.

- ``extractor_after_save(resource_dict, metadata_dict)`` is called after the
  metadata has been filtered and stored in the database but before it is
  indexed. ``metadata_dict`` is a dict-representation of a
  ``ckanext.extractor.model.ResourceMetadata`` instance and contains both the
  extracted metadata and information about the extraction process
  (meta-metadata, so to speak).

- ``extractor_after_index(resource_dict, metadata_dict)`` is called at the very
  end of the extraction process, after the metadata has been extracted,
  filtered, stored and indexed.


Adjust the download request
===========================
The ``ckanext.extractor.interfaces.IExtractorRequest`` interface can be
used to alter the request made to download the file for extraction. A typical
use case would be to add headers, that the remote server requires or to change
the URL.

The interface offers 1 hook:

- ``extractor_before_request(request)`` is called before the request
  is send to download the file for extraction. The ``request`` parameter
  is a ``PreparedRequest`` object
  `from the requests library <http://docs.python-requests.org/en/master/user/advanced/#prepared-requests>`_.


Development
===========

::

    . /usr/lib/ckan/default/bin/activate
    git clone https://github.com/stadt-karlsruhe/ckanext-extractor.git
    cd ckanext-extractor
    python setup.py develop
    pip install -r dev-requirements.txt


Running the Tests
-----------------
To run the tests, activate your CKAN virtualenv and do::

    ./runtests.sh

Any additional arguments are passed on to ``nosetests``.


License
=======
Copyright (C) 2016 Stadt Karlsruhe (www.karlsruhe.de)

Distributed under the GNU Affero General Public License. See the file
``LICENSE`` for details.


Changes
=======

0.2.0
-----
* Added ``IExtractorPostprocessor`` interface for postprocessing extraction
  results
* Fixed logging problems in ``paster`` commands

0.1.0
-----
* First release

