# create a user group with Administrator access
# create a user and add user to the group
# in the user tab, create an access key

import botocore.session
import os
import boto3
from dotenv import load_dotenv

############################################## CONNECTION FOR PROGRAMMATIC ACCESS #################################################
session = botocore.session.Session()

# paste access key and secret key in .env file
# make sure the credentials are written ex: Access_key="AHGJHSDGJSDGjag"
load_dotenv()

# call os.getenv to get value
initial_credentials = {
    "aws_access_key_id": os.getenv("Access_key"),
    "aws_secret_access_key": os.getenv("Secret_key"),
}

print(
    "############################## PROGRAMMATIC ACCESS ####################################"
)
print("Boto3 user connecting ...")

sts_client = boto3.client("sts", **initial_credentials)

role = os.getenv("ROLE")
session_name = "Boto3Session"

session.set_credentials(
    access_key=initial_credentials["aws_access_key_id"],
    secret_key=initial_credentials["aws_secret_access_key"],
)

print("SETTING CONNECTION WITH CREDENTIALS ...")
print("access_key_id:", session.get_credentials().access_key)
print("secret_access_key:", session.get_credentials().secret_key)
print("session_token:", session.get_credentials().token)


ec2_client = session.create_client("ec2", region_name="ca-central-1")

############################################### SECURITY GROUP CREATION ############################################
print(
    "############################## SECURITY GROUP CREATION FOR RESOURCES ####################################"
)
# all resources linked to an account is in a Virtual Private Cloud (VPC)
# it is used to isolate resources in there corresponding region

# list all of the VPC of my account
response_vpcs = ec2_client.describe_vpcs()

# gets the first virtual private network's id found
vpc_id = response_vpcs.get("Vpcs", [{}])[0].get("VpcId", "")
print("first virtual private cloud:", vpc_id)

# creates a security group for the given vpc that acts like a firewall
response_security_group = ec2_client.create_security_group(
    GroupName="ec2-security-group",
    Description="this acts like a firewall to control inbound and outbound from and to resources ",
    VpcId=vpc_id,
)

security_group_id = response_security_group["GroupId"]
print("security group created with id:", security_group_id)


# define rules for traffic of the security group
ec2_client.authorize_security_group_ingress(
    GroupId=security_group_id,
    IpPermissions=[
        {
            "IpProtocol": "tcp",
            "FromPort": 80,  # security group allows traffic from port 80 (HTTP)
            "ToPort": 80,  # port 80 traffic will reach resources
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],  # allows traffic from any source
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 22,  # security group allows traffic from port 22 (SSH)
            "ToPort": 22,  # port 80 traffic will reach resources
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],  # allows traffic from any source
        },
    ],
)


############################################### EC2 CREATION #######################################################
print(
    "############################## EC2 CREATION ####################################"
)

instance_params = {
    "ImageId": "ami-0d8270d86f77e72b2",  # found when done manually with aws UI needs to be same id as offered region
    "InstanceType": "t2.micro",
    "MinCount": 1,  # how many instance is created
    "MaxCount": 1,
}

response = ec2_client.run_instances(**instance_params)
print(
    "creating ec2 "
    + instance_params["MinCount"]
    + " instances of type "
    + instance_params["InstanceType"]
    + " with image id:"
    + instance_params["ImageId"]
)

print(response["Instances"][0]["InstanceId"])
