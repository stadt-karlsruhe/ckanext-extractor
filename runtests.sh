#!/bin/sh

# Run the tests for ckanext-extractor.
#
# Any arguments are forwarded to nosetests.

nosetests --ckan --with-pylons=test.ini $@

