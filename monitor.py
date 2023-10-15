from datetime import datetime, timedelta
import json
import time
import botocore.session
from dotenv import load_dotenv
import os

from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from metric_data import Metric_data
from datetime import datetime

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

print(
    "############################################### APPLICATION LOAD BALANCER REQUEST COUNT METRIC #######################################################"
)

load_balancer_list_metric_response = cloud_watch_client.list_metrics(
    Namespace="AWS/ApplicationELB",  # name of the container that groups metric of ApplicationELB together
    MetricName="RequestCount",  # metric name
    Dimensions=[
        {
            "Name": "LoadBalancer",
            # "Value": "the-cool-balancer"
        }
    ],
)

# list of metrics for a load balancer
# print(json.dumps(load_balancer_list_metric_response, indent=4))
print()

print(
    "################################################### TARGET GROUPS REQUEST COUNT METRIC ################################################################"
)

target_group_list_metric_response = cloud_watch_client.list_metrics(
    Namespace="AWS/ApplicationELB",
    MetricName="RequestCount",
    Dimensions=[{"Name": "TargetGroup"}],
)

# print(json.dumps(target_group_list_metric_response, indent=4))
print()
################################################### SPECIFICS ON THE REQUEST COUNT METRIC #########################################

print(
    "################################################### SPECIFICS ON THE REQUEST COUNT METRIC #############################################################"
)

(
    load_balancer_dimension,
    cluster1_target_group_dimension,
    cluster2_target_group_dimension,
) = (None, None, None)


# {
#     "Namespace": "AWS/ApplicationELB",
#     "MetricName": "RequestCount",
#     "Dimensions": [
#         {
#             "Name": "TargetGroup",
# HERE-->     "Value": "targetgroup/cluster-1-target-group/773e4bba0868d8a5"
#         },
#         {
#             "Name": "LoadBalancer",
#             "Value": "app/the-cool-balancer/78c769a279362fe0"
#         }
#     ]
# },

# have to check the print above to know structure of the metric response json
# finds the corresponding dimension in the json for each
# if the a part of the component's name is in the Value of the first element in Dimensions
# consider it the dimension of the component
for response in load_balancer_list_metric_response["Metrics"]:
    dimension = response["Dimensions"][0]
    if "app/the-cool-balancer" in dimension["Value"]:
        load_balancer_dimension = dimension

for response in target_group_list_metric_response["Metrics"]:
    dimension = response["Dimensions"][0]
    if "targetgroup/cluster-1-target-group" in dimension["Value"]:
        cluster1_target_group_dimension = dimension
    elif "targetgroup/cluster-2-target-group" in dimension["Value"]:
        cluster2_target_group_dimension = dimension

print()
print("load balancer dimension:", load_balancer_dimension)
print("cluster1 target group dimension:", cluster1_target_group_dimension)
print("cluster2 target group dimension:", cluster2_target_group_dimension)
print()


#################################################### CONSTRUCT PIPELINE ##########################################################
print(
    "##################################################### PIPELINE ###############################################################"
)

TARGET_GROUP_CLOUDWATCH_METRICS = ["RequestCountPerTarget"]
ELB_CLOUDWATCH_METRICS = ["NewConnectionCount", "ProcessedBytes", "TargetResponseTime"]
EC2_CLOUDWATCH_METRICS = ["CPUUtilization", "NetworkIn", "NetworkOut"]

# array of tuples for the 2 target groups and the load balancer
# id, dimensions, metrics
metric_pipeline = [
    ("1", cluster1_target_group_dimension, TARGET_GROUP_CLOUDWATCH_METRICS),
    ("2", cluster2_target_group_dimension, TARGET_GROUP_CLOUDWATCH_METRICS),
    ("", load_balancer_dimension, ELB_CLOUDWATCH_METRICS),
]

# add all the tuples for the ec2 instances
metric_pipeline += [
    (
        instanceId.split("-")[1],
        {"Name": "InstanceId", "Value": instanceId},
        EC2_CLOUDWATCH_METRICS,
    )
    for instanceId in cluster1_instance_ids
]
metric_pipeline += [
    (
        instanceId.split("-")[1],
        {"Name": "InstanceId", "Value": instanceId},
        EC2_CLOUDWATCH_METRICS,
    )
    for instanceId in cluster2_instance_ids
]

# print("pipeline", json.dumps(metric_pipeline, indent=4))
print()

# metric_pipeline
# [
# 1                 {'Name': 'TargetGroup',  'Value': 'targetgroup/cluster-1-target-group/9faea4e71b0906c7'} ['RequestCountPerTarget'],
# 2                 {'Name': 'TargetGroup',  'Value': 'targetgroup/cluster-2-target-group/3b5bef5a22a7c671'} ['RequestCountPerTarget'],
#                   {'Name': 'LoadBalancer', 'Value': 'app/the-cool-balancer/0eea9ebf5be40f22'}              ['NewConnectionCount', 'ProcessedBytes', 'TargetResponseTime'],
# 03c8cb3025d6eac6a {'Name': 'InstanceId',   'Value': 'i-03c8cb3025d6eac6a'}                                 ['CPUUtilization', 'NetworkIn', 'NetworkOut'],
# 00c42ee8786627b66 {'Name': 'InstanceId',   'Value': 'i-00c42ee8786627b66'}                                 ['CPUUtilization', 'NetworkIn', 'NetworkOut'],
# 01aa0442551550167 {'Name': 'InstanceId',   'Value': 'i-01aa0442551550167'}                                 ['CPUUtilization', 'NetworkIn', 'NetworkOut'],
# 02028fa41369ea6a5 {'Name': 'InstanceId',   'Value': 'i-02028fa41369ea6a5'}                                 ['CPUUtilization', 'NetworkIn', 'NetworkOut'],
# 06697ac91119cba0d {'Name': 'InstanceId',   'Value': 'i-06697ac91119cba0d'}                                 ['CPUUtilization', 'NetworkIn', 'NetworkOut'],
# 0509d88fa2b3e2256 {'Name': 'InstanceId',   'Value': 'i-0509d88fa2b3e2256'}                                 ['CPUUtilization', 'NetworkIn', 'NetworkOut'],
# ]

#################################################### BUILD METRIC QUERY ##########################################################
print(
    "#################################################### METRIC QUERY ###############################################################"
)

metricDataQy = []

for metric_action in metric_pipeline:
    # metric_actions[2]=metrics=['CPUUtilization', 'NetworkIn', 'NetworkOut'] check above
    for metric in metric_action[2]:
        if metric in EC2_CLOUDWATCH_METRICS:
            namespace = "AWS/EC2"
        else:
            namespace = "AWS/ApplicationELB"

        metricDataQy.append(
            # metric_action[0]=cluster id, metric_action[1]=dimension
            {
                "Id": (metric + metric_action[1]["Name"] + metric_action[0]).lower(),
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,  # set in if else
                        "MetricName": metric,  # each metric in the metrics array
                        "Dimensions": [
                            {
                                # dimension={'Name': 'InstanceId',   'Value': 'i-0509d88fa2b3e2256'}
                                "Name": metric_action[1]["Name"],
                                "Value": metric_action[1]["Value"],
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Sum",
                },
            }
        )

# [
# {
#         "Id": "requestcountpertargettargetgroup1",
#         "MetricStat": {
#             "Metric": {
#                 "Namespace": "AWS/ApplicationELB",
#                 "MetricName": "RequestCountPerTarget",
#                 "Dimensions": [
#                     {
#                         "Name": "TargetGroup",
#                         "Value": "targetgroup/cluster-1-target-group/9faea4e71b0906c7"
#                     }
#                 ]
#             },
#             "Period": 60,
#             "Stat": "Sum"
#         }
# },
# ...]

# print(json.dumps(metricDataQy, indent=4))
print()

query_response = cloud_watch_client.get_metric_data(
    MetricDataQueries=metricDataQy,
    StartTime=datetime.utcnow() - timedelta(minutes=30),
    EndTime=datetime.utcnow(),
)

# this is not completely a string but can be printed in terminal it is HTTP response can see status 200 and others
# can see what it looks like in metric_query_response.png
# the metric data are stored in the key "MetricDataResults"
# print("query response", query_response)
results = query_response["MetricDataResults"]

for metric in results:
    print(metric)
    print()


# new list from index 0 to index len(TARGET_GROUP_CLOUDWATCH_METRICS)-1=0
# basically [0] can also view that the id is indeed "requestcountpertargettargetgroup1"
cluster1_target_group_metrics = results[: len(TARGET_GROUP_CLOUDWATCH_METRICS)]

# [1:2] aka [1]
cluster2_target_group_metrics = results[
    len(TARGET_GROUP_CLOUDWATCH_METRICS) : 2 * len(TARGET_GROUP_CLOUDWATCH_METRICS)
]

# [2:2+3]=[2:5]=[2],[3],[4]
load_balancer_metrics = results[
    2 * len(TARGET_GROUP_CLOUDWATCH_METRICS) : 2 * len(TARGET_GROUP_CLOUDWATCH_METRICS)
    + len(ELB_CLOUDWATCH_METRICS)
]

# [2+3:end]=[5],...
ec2_instances_metrics = results[
    2 * len(TARGET_GROUP_CLOUDWATCH_METRICS) + len(ELB_CLOUDWATCH_METRICS) :
]

# each metric has id of metric name followed by instance id
print("cluster1_target_metrics", cluster1_target_group_metrics)
print(
    "###########################################################################################################################"
)
print("cluster2_target_metrics", cluster2_target_group_metrics)
print(
    "###########################################################################################################################"
)
print("load_balancer_metrics", load_balancer_metrics)
print(
    "###########################################################################################################################"
)

# an array of metrics=[{cpu_utilisation1},{network_in1},{network_out1},{cpu_utilisation2},{network_in2},{network_out2}]
print("ec2_metrics", ec2_instances_metrics)
print()
print(
    "#################################### SEPARATES METRICS PER COMPONENT ################################################"
)


# only needed for ec2 instances since all their metrics are in one big array
# seperates them into metrics per instances
def group_metrics_per_component(all_metrics, single_component_metrics):
    grouped_metrics = []
    i = 0
    while i < len(all_metrics):
        group = []
        for _ in range(len(single_component_metrics)):
            group.append(all_metrics[i])
            i += 1
        grouped_metrics.append(group)
    return grouped_metrics


# converts ec2 metrics into an array of array
# grouped_ecs_metrics=[
#    [{cpu_utilisation1},{network_in1},{network_out1}],    first ec2 instance
#    [{cpu_utilisation2},{network_in2},{network_out2}]     second ec2 instance
# ]
grouped_ecs_metrics = group_metrics_per_component(
    ec2_instances_metrics, EC2_CLOUDWATCH_METRICS
)
print("grouped_ec2_instances", grouped_ecs_metrics)
print(
    "#########################################################################################################################"
)


def generate_metric_groups_graphs(metric_groups, bar=False):
    # metric_groups[0] takes the array containing metrics of 1 component
    # to generalize function we also put a global array for cluster and load balancer even if the metrics are already for them alone
    # is needed to access one ec2 instance's metrics
    for i in range(len(metric_groups[0])):
        # convert every metric inside the array into Metric_data objects and store them in an array
        data_groups = [Metric_data(group[i]) for group in metric_groups]
        print("data group", data_groups)

        # takes first metric object in array
        label = data_groups[0].label
        print("data_groups[0]", data_groups[0])

        # creates a new figure and axe
        fig, ax = plt.subplots()
        if not bar:
            # set x axis to be in time hour:minute:second
            formatter = DateFormatter("%H:%M:%S")
            ax.xaxis.set_major_formatter(formatter)
            plt.xlabel("Timestamps")
        else:
            # set x axis to be instances
            plt.xlabel("Instances")

        for data in data_groups:
            if not bar:
                # If bar is False (not bar), it uses plt.plot to create a line plot using the timestamps
                # and values from the data object. It assigns a label to the plot based on the grouplabel
                # attribute of the metric_data object
                plt.plot(
                    data.timestamps,
                    data.values,
                    label=getattr(
                        data, "grouplabel", None
                    ),  # classify in group depending on the grouplabel
                )
            else:
                time.sleep(10)
                if data.values:
                    plt.bar(data.grouplabel, data.values[0])
                    # creates bar chart where each group label is an instance and takes the first value as height

        if not bar:
            plt.title(label)
        else:
            plt.title("Average " + label)

        if len(data_groups) > 1 and not bar:
            plt.legend(loc="best")

        plt.xticks(rotation=90)  # rotates the values on x axis to be a vertical line
        plt.tight_layout()  # This function adjusts the subplot parameters to ensure that all elements in the plot fit within the figure area properly
        plt.savefig(f"graphs/{label}")
        plt.close()


# each is an array that contains one or more metrics
# cluster1_target_group_metrics=
# [
#     {
#         "Id": "requestcountpertargettargetgroup1",
#         "Label": "AWS/ApplicationELB targetgroup/cluster-1-target-group/8ff85300e78f74c8 RequestCountPerTarget",
#         "Timestamps": [datetime(2023, 10, 15, 18, 39)],
#         "Values": [0.0],
#         "StatusCode": "Complete",
#     }
# ]
print(
    "############################################## GRAPH CLUSTERS #########################################################"
)
generate_metric_groups_graphs(
    [cluster1_target_group_metrics, cluster2_target_group_metrics]
)
print()
print(
    "############################################## GRAPH LOAD BALANCER #########################################################"
)
generate_metric_groups_graphs([load_balancer_metrics])
print()
print(
    "############################################## GRAPH EC2 instances #########################################################"
)
generate_metric_groups_graphs(grouped_ecs_metrics, True)
