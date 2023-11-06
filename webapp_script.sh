#!/bin/bash

sudo apt update -y
sudo apt upgrade -y

sudo groupadd csye6225g
sudo useradd -s /bin/false -g csye6225g -d /opt/csye6225 -m csye6225

sudo apt install software-properties-common -y
sudo apt install telnet -y
sudo apt install python3.11-venv  -y
sudo apt install unzip  -y

sudo wget https://amazoncloudwatch-agent.s3.amazonaws.com/debian/amd64/latest/amazon-cloudwatch-agent.deb 
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

sudo apt-get install collectd -y
sudo unzip ~/webapp.zip -d /opt/csye6225/webapp

python3 -m venv /home/admin/cs_env

 . /home/admin/cs_env/bin/activate
#rm -rf ~/webapp.zip
cd /opt/csye6225/webapp

pip install -r requirements.txt

sudo chown -R csye6225:csye6225g /opt/csye6225/webapp/
#chown -R csye6225:csye6225g /opt/csye6225/cs_env/

sudo cp /opt/csye6225/webapp/csye6225.service /etc/systemd/system/csye6225.service

sudo cp /opt/csye6225/webapp/cloudwatch-config.json /opt/cloudwatch-config.json
sudo chmod 644 /etc/systemd/system/csye6225.service
sudo systemctl daemon-reload
        
sudo systemctl enable csye6225
sudo systemctl start csye6225
sudo systemctl status csye6225


sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/cloudwatch-config.json -s


echo " End of AMI creation script"