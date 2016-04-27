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

Activate your CKAN virtualenv::

    . /usr/lib/ckan/default/bin/activate

Install *ckanext-extractor*::

    pip install ckanext-extractor

Open your CKAN configuration file (e.g. ``/etc/ckan/default/production.ini``)
and add ``extractor`` to the list of plugins::

    plugins = ... extractor

*ckanext-extractor* uses Celery background tasks to perform the extraction. You
therefore need to make sure that Celery is running, for example using

::
    paster --plugin=ckan celeryd -c /etc/ckan/default/production.ini

See the `CKAN documentation`_ for more information on Celery.

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
.. _`official_release`: http://archive.apache.org/dist/lucene/solr

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

Finally, restart your CKAN server. For example, if you're using Apache on
Ubuntu/Debian::

    sudo service apache2 restart

The installation is now complete. To verify that everything is working open the
URL ``/api/3/action/extractor_metadata_list``, e.g. via

::
    wget http://localhost/api/3/extractor_metadata_list

The output should look like this::

    FIXME


.. _`CKAN_documentation`: http://docs.ckan.org/en/latest/maintaining/background-tasks.html


Configuration
=============
ckanext-extractor can be configured via the usual CKAN configuration file (e.g.
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

    ckanext-extractor normalizes the field names reported by Solr by replacing
    underscores (``_``) with hyphens (``-``).


ToDo
====
- Add a way to update the resource's metadata using the extraction results.



Development
===========
To install ckanext-extractor for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/torfsen/ckanext-extractor.git
    cd ckanext-extractor
    python setup.py develop
    pip install -r dev-requirements.txt


Running the Tests
=================
To run the tests, activate your CKAN virtualenv and do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.extractor --cover-inclusive --cover-erase --cover-tests


---------------------------------
Registering ckanext-extractor on PyPI
---------------------------------

ckanext-extractor should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-extractor. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-extractor
----------------------------------------

ckanext-extractor is availabe on PyPI as https://pypi.python.org/pypi/ckanext-extractor.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags
