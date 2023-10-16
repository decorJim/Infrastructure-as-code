import time
import botocore.session
from dotenv import load_dotenv
import os
import requests
import threading


def consumeGETRequestSync(url: str):
    headers = {"content-type": "application/json"}

    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            data = response.text
            print(data)
            return response
    except requests.RequestException as e:
        print(f"Error encountered while making the HTTP request to {url}: {e}")
        return None


############################################## CONNECTION TO ACCOUNT #####################################################

session = botocore.session.Session()

load_dotenv()

initial_credentials = {
    "aws_access_key_id": os.getenv("Access_key"),
    "aws_secret_access_key": os.getenv("Secret_key"),
}

session.set_credentials(
    access_key=initial_credentials["aws_access_key_id"],
    secret_key=initial_credentials["aws_secret_access_key"],
)

######################################### LOAD BALANCER CLIENT CREATION #########################################################

load_balancer_client = session.create_client("elbv2", region_name="ca-central-1")
load_balancer_describe_response = load_balancer_client.describe_load_balancers(
    Names=["the-cool-balancer"]  # line 191
)

load_balancer_dns = load_balancer_describe_response["LoadBalancers"][0]["DNSName"]

############################################# first workload #########################################################

print("start workload 1 ...")
url_cluster1 = "http://" + load_balancer_dns + "/cluster1"

for _ in range(1000):
    t = threading.Thread(target=consumeGETRequestSync, args=(url_cluster1,))
    t.start()

print("workload 1 completed !!!")


############################################# second workload #########################################################

print("start workload 2 ...")
url_cluster2 = "http://" + load_balancer_dns + "/cluster2"

for _ in range(500):
    t = threading.Thread(target=consumeGETRequestSync, args=(url_cluster2,))
    t.start()

time.sleep(60)

for _ in range(1000):
    t = threading.Thread(target=consumeGETRequestSync, args=(url_cluster2,))
    t.start()

time.sleep(
    120
)  # needs to wait a bit before running monitor.py else metrics wont be available yet adjust if not all instance in graph prob longer
