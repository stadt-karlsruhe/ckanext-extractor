.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/torfsen/ckanext-extractor.svg?branch=master
    :target: https://travis-ci.org/torfsen/ckanext-extractor

.. image:: https://coveralls.io/repos/torfsen/ckanext-extractor/badge.svg
  :target: https://coveralls.io/r/torfsen/ckanext-extractor

.. image:: https://pypip.in/download/ckanext-extractor/badge.svg
    :target: https://pypi.python.org/pypi//ckanext-extractor/
    :alt: Downloads

.. image:: https://pypip.in/version/ckanext-extractor/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-extractor/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/ckanext-extractor/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-extractor/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/ckanext-extractor/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-extractor/
    :alt: Development Status

.. image:: https://pypip.in/license/ckanext-extractor/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-extractor/
    :alt: License


ckanext-extractor
#################
A CKAN_ extension for automatically extracting text and metadata from datasets.

*ckanext-extractor* extracts text and metadata from your datasets' resources
and adds them to the search index so that they can be used to find your data.

.. _CKAN: https://www.ckan.org


Requirements
============
*ckanext-extractor* has been developed and tested with CKAN 2.5.2. Other
versions may or may not work, please share your experiences by `creating an
issue <FIXME>`_.


Installation
============
.. note::

    The following steps assume a standard CKAN source installation.

Install Python Package
----------------------
Activate your CKAN virtualenv::

    . /usr/lib/ckan/default/bin/activate

Install *ckanext-extractor*::

    pip install ckanext-extractor

Open your CKAN configuration file (e.g. ``/etc/ckan/default/production.ini``)
and add ``extractor`` to the list of plugins::

    plugins = ... extractor


Start Celery Daemon
-------------------
*ckanext-extractor* uses Celery background tasks to perform the extraction. You
therefore need to make sure that Celery is running, for example using

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

.. note::

    The Solr packages on Ubuntu are broken_ and do not contain the necessary
    files. You can simply download an `official release`_ of the same version,
    unpack it to a suitable location (without installing it) and adjust the
    ``dir`` arguments in the configuration lines above accordingly.

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
Finally, restart your CKAN server. For example, if you're using Apache on
Ubuntu/Debian::

    sudo service apache2 restart


Test Installation
-----------------
The installation is now complete. To verify that everything is working open the
URL ``/api/3/action/extractor_list``, e.g. via

::

    wget -qO - http://localhost/api/3/action/extractor_list

The output should look like this (in particular, ``success`` should ``true``)::

    {"help": "http://localhost/api/3/action/help_show?name=extractor_list", "success": true, "result": []}


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

    ckanext.extractor.indexed_fields = contents author

The fulltext of a document is available via the ``contents`` field. Field names
are case-insensitive. You can use wildcards (``*`` and ``?``) to match multiple
field names. To index all fields simply set

::

    ckanext.extractor.indexed_fields = *

By default, only the fulltext of a document is indexed::

    ckanext.extractor.indexed_fields = contents

.. note::

    *ckanext-extractor* normalizes the field names reported by Solr by
    replacing underscores (``_``) with hyphens (``-``).


Paster Commands
===============
For administration purposes, metadata can be managed from the command line
using the paster_ tool.

.. _paster: http://docs.ckan.org/en/latest/maintaining/paster.html

.. note::

    You have to activate your virtualenv before you can use these commands::

        . /usr/lib/ckan/default/bin/activate

The general form for a paster command is

::

    paster --plugin=ckanext-extractor COMMAND ARGUMENTS --config=/etc/ckan/default/development.ini

Replace ``COMMAND`` and ``ARGUMENTS`` as described below.

The following commands are available:

:delete (all | ID [ID [...]]): Delete metadata. You can specify one or more
    resource IDs or a single ``all`` argument (in which case all metadata is
    deleted).

:extract [--force] (all | ID [ID [...]]): Extract metadata. You can specify one
    or more resource IDs or a single ``all`` argument (in which case metadata is
    extracted from all resources with appropriate formats). An optional
    ``--force`` argument can be used to force extraction if the resource format
    is ignored, if the resource is unchanged, or if another extraction job
    already has been scheduled for that resource.

    Note that this command only schedules the necessary extraction background
    tasks. The Celery daemon has to be running for the extraction to actually
    happen.

:list: List the IDs of all resources for which metadata has been extracted.

:show (all | ID [ID [...]]): Show extracted metadata. You can specify one or
    more resource IDs or a single ``all`` argument (in which case all metadata
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

:force: Optional boolean flag to force extraction if the resource format
    is ignored, if the resource is unchanged, or if an extraction task has
    already been scheduled for that resource.

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
    regardless of the status reported.

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


Development
===========
To install *ckanext-extractor* for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/torfsen/ckanext-extractor.git
    cd ckanext-extractor
    python setup.py develop
    pip install -r dev-requirements.txt


Running the Tests
=================
To run the tests, activate your CKAN virtualenv and do::

    ./runtests.sh

Any additional arguments are passed on to ``nosetests``.

