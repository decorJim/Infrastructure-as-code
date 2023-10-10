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

# list all of the VPC of my account, normally some are already created during account creation
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

##################################################### Attach rules to security group #################################################

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
print("rules assigned to security group ...")

############################################### SCRIPT to install app in instance ###############################################

app_script_content_cluster1 = open("install_app_1.sh", "r").read()
app_script_content_cluster2 = open("install_app_2.sh", "r").read()

print("script loaded ...")

############################################### EC2 CREATION #######################################################
print(
    "############################## EC2 CREATION ####################################"
)

# cluster 1 creation
instance_params_cluster1 = {
    "ImageId": "ami-0d8270d86f77e72b2",  # found when done manually with aws UI needs to be same id as offered region
    "InstanceType": "t2.micro",
    "MinCount": 3,  # how many instance is created
    "MaxCount": 3,
    "UserData": app_script_content_cluster1,
    "SecurityGroupIds": [security_group_id],
}

cluster_1_response = ec2_client.run_instances(**instance_params_cluster1)
print(
    "creating ec2 cluster1 "
    + str(instance_params_cluster1["MinCount"])
    + " instances of type "
    + str(instance_params_cluster1["InstanceType"])
    + " with image id:"
    + str(instance_params_cluster1["ImageId"])
)

instance_ids_cluster1 = [
    instance["InstanceId"] for instance in cluster_1_response["Instances"]
]
print("Created instances in cluster 1:", instance_ids_cluster1)

# cluster 2 creation
instance_params_cluster2 = {
    "ImageId": "ami-0d8270d86f77e72b2",  # found when done manually with aws UI needs to be same id as offered region
    "InstanceType": "t2.large",
    "MinCount": 3,  # how many instance is created
    "MaxCount": 3,
    "UserData": app_script_content_cluster2,
    "SecurityGroupIds": [security_group_id],
}

cluster_2_response = ec2_client.run_instances(**instance_params_cluster2)
print(
    "creating ec2 cluster 2 "
    + str(instance_params_cluster1["MinCount"])
    + " instances of type "
    + str(instance_params_cluster1["InstanceType"])
    + " with image id:"
    + str(instance_params_cluster1["ImageId"])
)

instance_ids_cluster2 = [
    instance["InstanceId"] for instance in cluster_2_response["Instances"]
]
print("Created instances in cluster 2:", instance_ids_cluster2)

################################################## LOAD BALANCER CREATION ############################################################

print(
    "############################## LOAD BALANCER CREATION ####################################"
)

load_balancer_client = session.create_client("elbv2", region_name="ca-central-1")

# some of the subnets are already created by default during account creation
subnets_response = ec2_client.describe_subnets()

print("traffic will be distributed between those subnets ...")
subnets_id = []
for subnet in subnets_response["Subnets"]:
    subnets_id.append(subnet["SubnetId"])
    print("subnet id:", subnet["SubnetId"])
    print("VPC id:", subnet["VpcId"])
    print("availability zone:", subnet["AvailabilityZone"])
    print("CidrBlock:", subnet["CidrBlock"])
    print()

load_balancer_response = load_balancer_client.create_load_balancer(
    Name="the-cool-balancer",
    Subnets=subnets_id,
    SecurityGroups=[security_group_id],
    Scheme="internet-facing",
)


# arn is the unique id given to my load balancer once it is created
load_balancer_arn = load_balancer_response["LoadBalancers"][0]["LoadBalancerArn"]
print("load balancer arn:", load_balancer_arn)

load_balancer_describe_response = load_balancer_client.describe_load_balancers(
    Names=["the-cool-balancer"]
)

if (
    "LoadBalancers" in load_balancer_describe_response
    and len(load_balancer_describe_response["LoadBalancers"]) > 0
):
    alb_dns_name = load_balancer_describe_response["LoadBalancers"][0]["DNSName"]
    print("ALB DNS Name:", alb_dns_name)
else:
    print("ALB not found or no DNS name available.")

################################################## Target group creation #########################################################

cluster_1_target_group = load_balancer_client.create_target_group(
    Name="cluster-1-target-group",
    Protocol="HTTP",
    Port=80,
    VpcId=vpc_id,
)
# unique id of target group 1
cluster_1_target_group_arn = cluster_1_target_group["TargetGroups"][0]["TargetGroupArn"]

cluster_2_target_group = load_balancer_client.create_target_group(
    Name="cluster-2-target-group", Protocol="HTTP", Port=80, VpcId=vpc_id
)
# unique id of target group 2
cluster_2_target_group_arn = cluster_2_target_group["TargetGroups"][0]["TargetGroupArn"]

print("target groups created:")
print(cluster_1_target_group_arn)
print(cluster_2_target_group_arn)


################################################## Target registration #########################################################
registration_response_cluster_1 = load_balancer_client.register_targets(
    TargetGroupArn=cluster_1_target_group_arn,
    Targets=[
        {"Id": instance_id}
        for instance_id in instance_ids_cluster1  # converts the list into a dict with key Id
    ],
)

print("target group for cluster 1 registered...")

registration_response_cluster_2 = load_balancer_client.register_targets(
    TargetGroupArn=cluster_2_target_group_arn,
    Targets=[{"Id": instance_id} for instance_id in instance_ids_cluster2],
)

print("target group for cluster 2 registered...")

################################################# Create listeners #############################################################
http_listener_response = load_balancer_client.create_listener(
    DefaultActions=[
        {
            "Type": "forward",
            "TargetGroupArn": cluster_1_target_group_arn,
        }
    ],
    LoadBalancerArn=load_balancer_arn,
    Port=80,
    Protocol="HTTP",
)

listenerArn = (http_listener_response["Listeners"][0]["ListenerArn"],)
print("listener created with arn:", listenerArn)

################################################# CREATE FORWARD RULES #########################################################
forward_rule_cluster_1_response = load_balancer_client.create_rule(
    ListenerArn=listenerArn,
    Conditions=[
        {"Field": "path-pattern", "values": ["/cluster1"]},
    ],
    Priority=1,
    Actions=[
        {
            "Type": "forward",
            "ForwardConfig": {
                "TargetGroups": [
                    {
                        "TargetGroupArn": cluster_1_target_group_arn,
                        "Weight": 1,  # 1, which means that it has an equal share of the traffic when compared to other target groups (if multiple target groups are used).
                    },
                ],
                "TargetGroupStickinessConfig": {
                    "Enabled": False,  # stickiness, which is the persistence of client requests to a specific target group for a specified duration.
                },
            },
        }
    ],
)

forward_rule_cluster_2_response = load_balancer_client.create_rule(
    ListenerArn=listenerArn,
    Conditions=[
        {"Field": "path-pattern", "values": ["/cluster2"]},
    ],
    Priority=2,
    Actions=[
        {
            "Type": "forward",
            "ForwardConfig": {
                "TargetGroups": [
                    {
                        "TargetGroupArn": cluster_2_target_group_arn,
                        "Weight": 1,  # 1, which means that it has an equal share of the traffic when compared to other target groups (if multiple target groups are used).
                    },
                ],
                "TargetGroupStickinessConfig": {
                    "Enabled": False,  # stickiness, which is the persistence of client requests to a specific target group for a specified duration.
                },
            },
        }
    ],
)

print("forward rules created ...")
