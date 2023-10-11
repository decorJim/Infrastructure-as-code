#!/bin/bash

# Update package list and install necessary packages
sudo yum update -y
sudo yum install -y python3 python3-pip

sudo mkdir app
cd app

python3 -m venv venv
source venv/bin/activate

sudo pip install Flask

sudo echo '
from flask import Flask
import requests
import subprocess

app = Flask(__name__)

@app.route("/cluster2")
def get_instance_id():
    # Use the EC2 metadata service to fetch the instance ID
    try: 
        instance_id=subprocess.check_output(["ec2-metadata","-i"]).decode("utf-8").strip().split(":")[1].strip()
        print("Instance ID:", instance_id)
        return "Instance ID:" + str(instance_id)
    except subprocess.CalledProcessError as e:
        print("Error:", e)
    

@app.route("/health")
def health_check():
    # If everything is fine, return a 200 OK response when ping http://your-instance-ip:80/health
    return "OK", 200

# 0.0.0.0 allows incoming connections from any IP address
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
' > main.py

nohup sudo python3 main.py > /dev/null 2>&1 &

echo "Flask app is running on port 80"
