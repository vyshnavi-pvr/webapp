#!/bin/bash

sudo apt update
sudo apt upgrade

sudo apt install software-properties-common

sudo apt install python3.11-venv
python3 -m venv cs_env 
source cs_env/bin/activate

sudo apt install postgresql postgresql-contrib

sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql -c "CREATE ROLE myuser WITH LOGIN PASSWORD 'hello' SUPERUSER;"

sudo apt install unzip

cd ~/ && unzip webapp.zip -d webapp
pip install -r requirements.txt