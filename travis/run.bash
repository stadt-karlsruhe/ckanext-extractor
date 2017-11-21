#!/bin/bash
set -e

nosetests --ckan \
          --with-pylons=subdir/test.ini \
          --with-coverage \
          --cover-package=ckanext.extractor \
          --cover-erase \
          --cover-inclusive \
          ckanext

