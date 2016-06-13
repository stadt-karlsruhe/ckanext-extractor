#!/bin/sh

# Run the tests for ckanext-extractor.
#
# Any arguments are forwarded to nosetests.

# Create database tables if necessary
paster --plugin=ckanext-extractor init -c test.ini

# Run tests
nosetests --ckan \
          --with-pylons=test.ini \
          --with-coverage \
          --cover-package=ckanext.extractor \
          --cover-erase \
          --cover-inclusive \
          $@

