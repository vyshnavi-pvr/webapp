#!/bin/bash

sudo apt update -y
sudo apt upgrade -y

sudo apt install software-properties-common -y

sudo apt install python3.11-venv  -y
python3 -m venv cs_env 
. cs_env/bin/activate

sudo apt install postgresql postgresql-contrib  -y

sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql -c "CREATE ROLE myuser WITH LOGIN PASSWORD 'hello' SUPERUSER;"

sudo apt install unzip  -y

cd ~/ && unzip webapp.zip -d webapp
cd ~/webapp && pip install -r requirements.txt

sudo -u postgres psql -l

python main.py
