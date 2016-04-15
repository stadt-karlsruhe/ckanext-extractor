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

=============
ckanext-extractor
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!


------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.

This extension requires Celery for running background jobs asynchronously.
Make sure that your Celery daemon is running:

    . /usr/lib/ckan/default/bin/activate
    paster --plugin=ckan celeryd -c /etc/ckan/default/production.ini


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-extractor:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-extractor Python package into your virtual environment::

     pip install ckanext-extractor

3. Add ``extractor`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload



Solr Configuration
------------------
`ckanext-extractor` uses CKAN's Apache Solr instance for two things:

- Extracting text and metadata from resource files

- Indexing the extracted information so that it can be used to find resources

Both of these require some changes to the Solr configuration.

By default, the necessary plugins for text and metadata extration are disabled
in Solr. To enable them, find your main Solr configuration file (usually
``/etc/solr/conf/solrconfig.xml``) and add/uncomment the following lines::

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
Solr index. To set up the necessary Solr fields, add the following lines to
your Solr schema configuration (usually ``/etc/solr/conf/schema.xml``)::

    # Directly before the line that says "</fields>"
    <dynamicField name="ckanext-extractor_*" type="text" indexed="true" stored="false"/>

    # Directly before the line that says "</schema>"
    <copyField source="ckanext-extractor_*" dest="text"/>

Make sure to restart Solr after you have applied the changes. For example, if
you're using Jetty as an application server for Solr::

    sudo service jetty restart


---------------
Config Settings
---------------

Document any optional config settings here. For example::

    # The minimum number of hours to wait before re-checking a resource
    # (optional, default: 24).
    ckanext.extractor.some_setting = some_default_value


------------------------
Development Installation
------------------------

To install ckanext-extractor for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/torfsen/ckanext-extractor.git
    cd ckanext-extractor
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

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
