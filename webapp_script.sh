#!/bin/bash

sudo apt update -y
sudo apt upgrade -y

sudo groupadd csye6225g
sudo useradd -s /bin/false -g csye6225g -d /opt/csye6225 -m csye6225

sudo apt install software-properties-common -y
sudo apt install telnet -y
sudo apt install python3.11-venv  -y
sudo apt install unzip  -y

sudo unzip ~/webapp.zip -d /opt/csye6225/webapp

python3 -m venv /home/admin/cs_env

 . /home/admin/cs_env/bin/activate
#rm -rf ~/webapp.zip
cd /opt/csye6225/webapp

pip install -r requirements.txt

sudo chown -R csye6225:csye6225g /opt/csye6225/webapp/
#chown -R csye6225:csye6225g /opt/csye6225/cs_env/

sudo cp /opt/csye6225/webapp/csye6225.service /etc/systemd/system/csye6225.service

sudo chmod 644 /etc/systemd/system/csye6225.service
sudo systemctl daemon-reload
        
sudo systemctl enable csye6225
sudo systemctl start csye6225
sudo systemctl status csye6225


echo " End of AMI creation script"