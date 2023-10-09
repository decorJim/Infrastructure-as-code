#!/bin/bash

# Update package list and install necessary packages
sudo yum update -y
sudo yum install -y python3 python3-pip

# Create app folder
mkdir app
cd app

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask
pip install Flask

# Create a Flask app
echo '
from flask import Flask
import requests

app = Flask(__name__)

@app.route("/")
def get_instance_id():
    # Use the EC2 metadata service to fetch the instance ID
    instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id").text
    return "Instance ID: " + str(instance_id)

@app.route("/health")
def health_check():
    # If everything is fine, return a 200 OK response when ping http://your-instance-ip:80/health
    return "OK", 200

# 0.0.0.0 allows incoming connections from any IP address
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
' > main.py

# Run the Flask app in the background
nohup python main.py > /dev/null 2>&1 &

echo "Flask app is running on port 80"
