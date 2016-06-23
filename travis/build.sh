#!/bin/bash
set -e

echo "This is travis-build.bash..."


echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install postgresql-$PGVERSION solr-tomcat libcommons-fileupload-java:amd64=1.2.2-1

echo "Downloading Solr plugins"
wget http://archive.apache.org/dist/lucene/solr/1.4.1/apache-solr-1.4.1.tgz
tar xzf apache-solr-1.4.1.tgz
sudo mv -v apache-solr-1.4.1 /var/apache-solr

echo "Configure Solr"
sudo cp -v travis/solr/* /etc/solr/conf/

echo "Restarting Tomcat"
sudo service tomcat6 restart

echo "Checking that Tomcat is up"
sudo service tomcat6 status
curl http://127.0.0.1:8080

echo "Checking that Solr is up"
curl http://127.0.0.1:8080/solr/admin/ping

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
export latest_ckan_release_branch=`git branch --all | grep remotes/origin/release-v | sort -r | sed 's/remotes\/origin\///g' | head -n 1`
echo "CKAN branch: $latest_ckan_release_branch"
git checkout $latest_ckan_release_branch
python setup.py develop
pip install -r requirements.txt --allow-all-external
pip install -r dev-requirements.txt --allow-all-external
cd -

echo "Installing ckanext-extractor and its requirements..."
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "Copying test-local.ini"
cp -v travis/test-local.ini subdir/

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "Initializing database for ckanext-extractor..."
paster --plugin=ckanext-extractor init -c subdir/test.ini

echo "travis-build.bash is done."

