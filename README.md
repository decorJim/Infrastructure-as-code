# Infrastructure-as-code

# clients
- to create an aws service, we must first create a client for each corresponding service

# monitor ec2 instance
- to check if the script was installed correctly on created ec2 instance
- connect to the ec2 instance:
- click on the instance id in "EC2 Dashboard"
- click on "connect" button
- in tab "EC2 instance connect"
- connection type is "Connect using EC2 Instance Connect"
- click on "Connect"
- by default the connection is in user folder, you want to go to root folder
- enter command "cd .." and log content with command "ls" until you go to root folder and find all files
- when you find "app" folder, go inside using command "cd app"
- make sure all files like "main.py" and and environment "venv" are created
- in another tab, go to instance's details and copy value of "Public IPv4 address" and paste it in a browser tab to check if app is running

# debug app error
- first deactivate the background run 
- use command [ ps aux | grep "python3 main.py" ] to find the process running in background
- use command "kill process_id"
- manually run the app using "python3 main.py"
- use browser to ping API and check error logs in the connect terminal

# aws listeners
- we attach listeners to the load balancer to tell how to route the traffic

# target groups
- we define target group and put resource associated with them
- the listener can then forward traffic to that group

# flask app
- for routing inside the application, we need to define as many routing as the number of cluster
- if 2 cluster then /cluster1 and /cluster2
- else the load balancer rules cannot be define automatically

# delete resource order
- sometimes will have to wait a bit for other resources to detect that their user resources are deleted
- delete all running instances
- delete the load balancer
- delete all target groups (found when click on a random running instance, check left side bar and scroll down)
- delete the security group

# MetricName
RequestCount: This metric represents the total number of requests handled by the load balancer.
HealthyHostCount: This metric counts the number of healthy instances behind the load balancer.
UnHealthyHostCount: This metric counts the number of unhealthy instances.
Latency: Measures the time it takes to complete a request.

# Dimensions
- specific on a metric
- The availability region
- The target group
- the resource

# uncomment json print when needed
- to check how a filter works uncomment the print json to see the full object

# graph
- if folder "graphs" is not created, created else code will crash