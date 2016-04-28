#!/bin/sh

# Run the tests for ckanext-extractor.
#
# Any arguments are forwarded to nosetests.

nosetests --ckan \
          --with-pylons=test.ini \
          --with-coverage \
          --cover-package=ckanext.extractor \
          --cover-erase \
          $@

