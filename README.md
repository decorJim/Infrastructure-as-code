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

