#!/bin/bash
set -e

echo "This is travis-build.bash..."

SOLR_VERSION=3.6.2

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install solr-tomcat=$SOLR_VERSION\*

echo "Downloading Solr plugins"
wget http://archive.apache.org/dist/lucene/solr/$SOLR_VERSION/apache-solr-$SOLR_VERSION.tgz
tar xzf apache-solr-$SOLR_VERSION.tgz
sudo mv -v apache-solr-$SOLR_VERSION /var/apache-solr

echo "Configure Solr"
sudo cp -v travis/solr/ckan-$CKANVERSION/* /etc/solr/conf/

echo "Restarting Tomcat"
sudo service tomcat6 restart

echo "Checking that Tomcat is up"
sudo service tomcat6 status
curl http://127.0.0.1:8080

echo "Checking that Solr is up"
curl http://127.0.0.1:8080/solr/admin/ping

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
pushd ckan
if [ $CKANVERSION == 'master' ]
then
    echo "CKAN version: master"
else
    CKAN_TAG=$(git tag | grep ^ckan-$CKANVERSION | sort --version-sort | tail -n 1)
    git checkout $CKAN_TAG
    echo "CKAN version: ${CKAN_TAG#ckan-}"

    if [ $CKANVERSION == '2.6' ]
    then
        echo "Installing ckanext-rq"
        pushd ..
        git clone https://github.com/ckan/ckanext-rq.git
        cd ckanext-rq
        python setup.py develop
        pip install -r requirements.txt
        cd ..
        # Add `rq` to the list of active CKAN plugins
        sed -i '/^\s*ckan.plugins\s*=/ s/$/ rq/' test.ini
        popd
    fi
fi
# Unpin CKAN's psycopg2 dependency get an important bugfix
# https://stackoverflow.com/questions/47044854/error-installing-psycopg2-2-6-2
sed -i '/psycopg2/c\psycopg2' requirements.txt
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt
popd

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "Installing ckanext-extractor and its requirements..."
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "Copying test-local.ini"
cp -v travis/test-local.ini subdir/

echo "Initialising the database..."
pushd ckan
paster db init -c test-core.ini
popd

echo "Initializing database for ckanext-extractor..."
paster --plugin=ckanext-extractor init -c subdir/test.ini

echo "travis-build.bash is done."

