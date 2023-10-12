import botocore.session
from dotenv import load_dotenv
import os

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

############################################## INSTANCE ID FROM TARGET GROUP #####################################################
# first cluster
load_balancer_client = session.create_client("elbv2", region_name="ca-central-1")

cluster1_target_group_name = "cluster-1-target-group"

target_groups = load_balancer_client.describe_target_groups(
    Names=[cluster1_target_group_name]
)

cluster1_target_group_arn = target_groups["TargetGroups"][0]["TargetGroupArn"]
targets_response = load_balancer_client.describe_target_health(
    TargetGroupArn=cluster1_target_group_arn
)

cluster1_instance_ids = [
    target["Target"]["Id"] for target in targets_response["TargetHealthDescriptions"]
]

# second cluster

cluster2_target_group_name = "cluster-2-target-group"

target_groups = load_balancer_client.describe_target_groups(
    Names=[cluster2_target_group_name]
)

cluster2_target_group_arn = target_groups["TargetGroups"][0]["TargetGroupArn"]
targets_response = load_balancer_client.describe_target_health(
    TargetGroupArn=cluster2_target_group_arn
)

cluster2_instance_ids = [
    target["Target"]["Id"] for target in targets_response["TargetHealthDescriptions"]
]

print("cluster 1 ids:", cluster1_instance_ids)
print("cluster 2 ids:", cluster2_instance_ids)

############################################## CLOUDWATCH SETUP ###################################################################

cloud_watch_client = session.create_client("cloudwatch", region_name="ca-central-1")

metric_data = []


# Define the metric entries for CPUUtilization, NetworkIn, and NetworkOut
for instanceId in cluster1_instance_ids:
    cpu_metric_entry = {
        "MetricName": "CPUUtilization",
        "Dimensions": [{"Name": "InstanceId", "Value": instanceId}],
    }
    metric_data.append(cpu_metric_entry)

print(metric_data[0])

# Put the metric data
cloud_watch_client.put_metric_data(
    Namespace="AWS/ApplicationELB", MetricData=[metric_data[0]]
)
