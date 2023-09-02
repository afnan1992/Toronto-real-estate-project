import boto3
import configparser
import pathlib
import sys
import os
import logging

"""
Part of DAG. Take Reddit data and upload to S3 bucket. Takes one command line argument of format YYYYMMDD. 
This represents the file downloaded from Reddit, which will be in the /tmp folder.
"""

# Load AWS credentials
parser = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
parser.read(f"{script_path}/configuration.conf")

BUCKET_NAME = parser.get("aws_config", "bucket_name")
AWS_REGION = parser.get("aws_config", "aws_region")
AWS_ACCESS_KEY = parser.get("aws_config","AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = parser.get("aws_config","AWS_SECRET_ACCESS_KEY")


# Name for our S3 file
def upload_to_s3(file,date):
    """Upload input file to S3 bucket"""
    conn = connect_to_s3()
    upload_file_to_s3(conn,file,date)


def connect_to_s3():
    """Connect to S3 Instance"""
    try:
        session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        s3 = session.resource('s3')
        return s3
    except Exception as e:
        print(f"Can't connect to S3. Error: {e}")
        sys.exit(1)


def upload_file_to_s3(conn,file,date):
    """Upload file to S3 Bucket"""
    basefile=os.path.basename(file)
    logging.info(basefile)
    folderpath = 'data/'+date+'/{}'
    #result = conn.Bucket(BUCKET_NAME).upload_file(file,'data/{}'.format(basefile))
    result = conn.Bucket(BUCKET_NAME).upload_file(file,folderpath.format(basefile))
    
        
    
