import botocore.session
from dotenv import load_dotenv
import os
import boto3

############################################## CONNECTION TO ACCOUNT #####################################################

session = botocore.session.Session()

load_dotenv()

initial_credentials = {
    "aws_access_key_id": os.getenv("Access_key"),
    "aws_secret_access_key": os.getenv("Secret_key"),
}

sts_client = boto3.client("sts", **initial_credentials)
